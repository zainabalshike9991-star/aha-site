import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'a_very_secret_key_123')

# إعدادات قاعدة البيانات (تقرأ رابط Render تلقائياً، وتستخدم SQLite للتجربة المحلية)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db').replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# تفعيل نظام الحماية CSRF (مثل موقع زميلك)
csrf = CSRFProtect(app)

# --- جداول قاعدة البيانات ---
class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization = db.Column(db.String(10))
    courses = db.Column(db.String(200))
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    classification = db.Column(db.String(100), nullable=False)
    identity = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    birthdate = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.String(200), nullable=False)

class SupportMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(120))
    body = db.Column(db.Text)

# --- مسارات الموقع ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        new_msg = SupportMessage(
            name=request.form.get('name'), 
            email=request.form.get('email'), 
            body=request.form.get('body')
        )
        db.session.add(new_msg)
        db.session.commit()
        return "<h1 style='text-align:center; font-family:sans-serif; margin-top:50px;'>تم إرسال رسالتك للدعم بنجاح</h1><div style='text-align:center;'><a href='/'>عودة للرئيسية</a></div>"
    return render_template('contact.html')

@app.route('/submit', methods=['POST'])
def submit():
    org = request.form.get('organization')
    courses_list = request.form.getlist('courses')
    courses_str = ", ".join(courses_list) if courses_list else "لا توجد دورات"
    
    new_reg = Registration(
        organization=org, 
        courses=courses_str,
        full_name=request.form.get('full_name'), 
        email=request.form.get('email'),
        classification=request.form.get('classification'), 
        identity=request.form.get('identity'),
        city=request.form.get('city'), 
        birthdate=request.form.get('birthdate'),
        phone=request.form.get('phone'), 
        notes=request.form.get('notes')
    )
    db.session.add(new_reg)
    db.session.commit()
    
    return "<h1 style='text-align:center; font-family:sans-serif; margin-top:50px;'>✅ تم إرسال طلبك بنجاح!</h1><div style='text-align:center;'><a href='/'>العودة للرئيسية</a></div>"

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin = Admin.query.first()
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
        return "<h1 style='text-align:center; font-family:sans-serif; margin-top:50px;'>كلمة المرور خاطئة!</h1><div style='text-align:center;'><a href='/admin/login'>حاول مرة أخرى</a></div>"
    return render_template('login.html')

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    regs = Registration.query.order_by(Registration.date.desc()).all()
    return render_template('dashboard.html', regs=regs)

@app.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

# --- إنشاء قاعدة البيانات وإعداد كلمة المرور عند أول تشغيل ---
with app.app_context():
    db.create_all()
    if not Admin.query.first():
        # كلمة المرور الافتراضية هي admin123 (يمكنك تغييرها من هنا لاحقاً)
        hashed_pw = generate_password_hash('admin123', method='pbkdf2:sha256')
        db.session.add(Admin(password_hash=hashed_pw))
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, redirect, url_for, session, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configuration for SQLite database and Flask-Mail 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'your_username'
app.config['MAIL_PASSWORD'] = 'your_password'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
mail = Mail(app)

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return "Welcome to the Home Page!"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('profile'))
        else:
            flash("Login failed. Please check your credentials.", "danger")
    return render_template('login.html')

@app.route('/profile')
@login_required
def profile():
    return f"Welcome to your profile, {current_user.username}!"

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Please choose a different one.", "danger")
        else:
            password_hash = generate_password_hash(password)
            new_user = User(username=username, email=email, password_hash=password_hash)
            db.session.add(new_user)
            db.session.commit()
            send_verification_email(new_user)
            flash("Registration successful! Please check your email for verification.", "success")
            return redirect(url_for('login'))
    return render_template('register.html')

def send_verification_email(user):
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
    user.is_verified = False
    db.session.commit()
    msg = Message('Verify your email', sender='your_email@example.com', recipients=[user.email])
    msg.body = f"Click the following link to verify your email: {url_for('verify', token=token, _external=True)}"
    mail.send(msg)

@app.route('/verify/<token>')
def verify(token):
    user = User.query.filter_by(is_verified=False).first()
    if user and token:
        user.is_verified = True
        db.session.commit()
        flash("Email verification successful! You can now log in.", "success")
        return redirect(url_for('login'))
    else:
        flash("Email verification failed. Please try again or contact support.", "danger")
        return redirect(url_for('login'))

if __name__ == '__main__':
    db.create_all()
    app.run()

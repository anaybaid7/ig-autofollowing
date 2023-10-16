from flask import Flask, request, redirect, url_for, session, render_template, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import os
import random
import string
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_bcrypt import Bcrypt
from flask_mail import Mail

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'your_username'
app.config['MAIL_PASSWORD'] = 'your_password'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Secret key for user token generation
app.config['PASSWORD_RESET_TIMEOUT'] = 3600  # Password reset token expiration time (1 hour)
app.config['MAX_PASSWORD_ATTEMPTS'] = 3  # Maximum number of incorrect password attempts before account lock
app.config['ACCOUNT_LOCK_DURATION'] = 3600  # Account lock duration (1 hour)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
mail = Mail(app)
bcrypt = Bcrypt(app)

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Register')

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    password_attempts = db.Column(db.Integer, default=0)
    role = db.Column(db.String(20), default="user")  # User role (default is "user")

class AdminView(ModelView):
    # Admin view to manage user accounts
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == "admin"

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == "admin"

admin = Admin(app, index_view=MyAdminIndexView(name='Admin Home'))
admin.add_view(AdminView(User, db.session))

login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return "Welcome to the Home Page!"

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Please choose a different one.", "danger")
        else:
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, email=email, password_hash=password_hash)
            db.session.add(new_user)
            db.session.commit()
            send_verification_email(new_user)
            flash("Registration successful! Please check your email for verification.", "success")
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            if user.is_locked:
                flash("Account is locked. Please contact support.", "danger")
            elif not user.is_verified:
                flash("Account not verified. Please check your email for verification instructions.", "warning")
            else:
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

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(user.email, salt='password-reset')
            reset_link = url_for('reset_password', token=token, _external=True)
            send_password_reset_email(user, reset_link)
            flash("Password reset instructions have been sent to your email.", "success")
        else:
            flash("No user found with that email address.", "danger")
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset', max_age=app.config['PASSWORD_RESET_TIMEOUT'])
        user = User.query.filter_by(email=email).first()
        if request.method == 'POST':
            password = request.form.get('password')
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            user.password_hash = password_hash
            db.session.commit()
            flash("Password reset successful. You can now log in with your new password.", "success")
            return redirect(url_for('login'))
        return render_template('reset_password.html', email=email)
    except SignatureExpired:
        flash("Password reset link has expired. Please request a new link.", "danger")
        return redirect(url_for('forgot_password'))

@app.route('/user_profile')
@login_required
def user_profile():
    return render_template('user_profile.html')

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        if bcrypt.check_password_hash(current_user.password_hash, current_password):
            password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            current_user.password_hash = password_hash
            db.session.commit()
            flash("Password change successful.", "success")
        else:
            flash("Current password is incorrect. Password not changed.", "danger")
    return redirect(url_for('user_profile'))

@app.route('/lock_account')
@login_required
def lock_account():
    if current_user.password_attempts >= app.config['MAX_PASSWORD_ATTEMPTS']:
        current_user.is_locked = True
        db.session.commit()
        flash("Your account has been locked due to too many incorrect password attempts. Contact support to unlock.", "danger")
        return redirect(url_for('logout'))
    return redirect(url_for('user_profile'))

def send_password_reset_email(user, reset_link):
    msg = Message('Password Reset', sender='your_email@example.com', recipients=[user.email])
    msg.html = f"Click the following link to reset your password: <a href='{reset_link}'>Reset Password</a>"
    mail.send(msg)

if __name__ == '__main__':
    db.create_all()
    app.run()

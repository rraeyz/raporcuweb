from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Kullanıcı bilgileri
    full_name = db.Column(db.String(120))
    credits = db.Column(db.Integer, default=0, nullable=False)
    
    # Durum bilgileri
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    force_password_change = db.Column(db.Boolean, default=False, nullable=False)
    
    # Token'lar
    email_verification_token = db.Column(db.String(100), unique=True)
    password_reset_token = db.Column(db.String(100), unique=True)
    password_reset_expires = db.Column(db.DateTime)
    
    # Tarih bilgileri
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    
    # İlişkiler
    reports = db.relationship('Report', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Şifreyi hashle ve kaydet"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Şifreyi kontrol et"""
        return check_password_hash(self.password_hash, password)
    
    def generate_email_verification_token(self):
        """E-posta doğrulama tokeni oluştur"""
        self.email_verification_token = secrets.token_urlsafe(32)
        return self.email_verification_token
    
    def generate_password_reset_token(self):
        """Şifre sıfırlama tokeni oluştur"""
        self.password_reset_token = secrets.token_urlsafe(32)
        from datetime import datetime, timedelta
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        return self.password_reset_token
    
    def verify_email(self):
        """E-postayı doğrula"""
        self.email_verified = True
        self.email_verification_token = None
    
    def add_credits(self, amount):
        """Kredi ekle"""
        self.credits += amount
    
    def deduct_credits(self, amount):
        """Kredi düş"""
        if self.credits >= amount:
            self.credits -= amount
            return True
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'

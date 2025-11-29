from app import db
from datetime import datetime

class Settings(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Site bilgileri
    site_name = db.Column(db.String(100), default='RaporcuWeb')
    site_description = db.Column(db.String(255))
    logo_url = db.Column(db.String(255))
    favicon_url = db.Column(db.String(255))
    
    # Tema ayarları
    theme_color = db.Column(db.String(7), default='#4e73df')  # Hex color
    theme_mode = db.Column(db.String(10), default='light')  # light, dark, auto
    
    # İletişim bilgileri
    contact_email = db.Column(db.String(120))
    support_email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    
    # Sosyal medya
    facebook_url = db.Column(db.String(255))
    twitter_url = db.Column(db.String(255))
    instagram_url = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(255))
    
    # Shopier ayarları
    shopier_payment_url = db.Column(db.String(500))  # Ana ödeme linki
    shopier_webhook_secret = db.Column(db.String(255))
    
    # Kredi ayarları
    default_report_cost = db.Column(db.Integer, default=1)  # Rapor başına kredi
    welcome_bonus_credits = db.Column(db.Integer, default=0)  # Yeni kayıt bonusu
    
    # Özellikler
    enable_registration = db.Column(db.Boolean, default=True)
    enable_email_verification = db.Column(db.Boolean, default=True)
    enable_password_reset = db.Column(db.Boolean, default=True)
    maintenance_mode = db.Column(db.Boolean, default=False)
    
    # AI Ayarları
    default_ai_model = db.Column(db.String(50), default='openai')  # openai, anthropic, google
    openai_api_key = db.Column(db.String(255))
    anthropic_api_key = db.Column(db.String(255))
    google_api_key = db.Column(db.String(255))
    
    # Tarih
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_settings():
        """Ayarları getir (singleton pattern)"""
        settings = Settings.query.first()
        if not settings:
            settings = Settings()
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def __repr__(self):
        return f'<Settings {self.site_name}>'

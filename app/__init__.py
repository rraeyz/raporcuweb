from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import config
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["10000 per day", "1000 per hour"],  # Çok yüksek limitler
    storage_uri="memory://"
)

def create_app(config_name='development'):
    """Flask uygulamasını oluştur ve yapılandır"""
    app = Flask(__name__)
    
    # Konfigürasyonu yükle
    app.config.from_object(config[config_name])
    
    # .env dosyasını yükle
    from dotenv import load_dotenv
    load_dotenv()
    
    # Eklentileri başlat
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Bu sayfaya erişmek için lütfen giriş yapın.'
    login_manager.login_message_category = 'warning'
    
    # HTTPS redirect (production'da)
    @app.before_request
    def redirect_to_https():
        """HTTP isteklerini HTTPS'e yönlendir (production'da)"""
        if not app.debug and not app.testing:
            from flask import request, redirect, url_for
            if request.url.startswith('http://'):
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)
    
    # Blueprint'leri kaydet
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.market import market_bp
    from app.routes.reports import reports_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(market_bp, url_prefix='/market')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Template filter'ları ekle
    from app.utils.helpers import format_datetime, format_currency, format_number
    app.jinja_env.filters['datetime'] = format_datetime
    app.jinja_env.filters['currency'] = format_currency
    app.jinja_env.filters['number'] = format_number
    
    # Veritabanı tablolarını oluştur
    with app.app_context():
        # TÜM modelleri import et ki db.create_all() çalışsın
        from app.models import (
            User, Report, Transaction, CreditPackage, 
            PromoCode, Announcement, Settings
        )
        db.create_all()
        init_default_data()
    
    return app

def init_default_data():
    """Varsayılan verileri oluştur"""
    from app.models.user import User
    from app.models.settings import Settings
    from app.models.credit_package import CreditPackage
    from werkzeug.security import generate_password_hash
    
    # Varsayılan admin kullanıcı
    admin = User.query.filter_by(email='admin@raporcuweb.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@raporcuweb.com',
            password_hash=generate_password_hash('Admin123!'),
            full_name='Admin',
            is_admin=True,
            is_active=True,
            email_verified=True,
            credits=1000
        )
        db.session.add(admin)
    
    # Varsayılan site ayarları
    settings = Settings.query.first()
    if not settings:
        settings = Settings(
            site_name='RaporcuWeb',
            site_description='Yapay Zeka Destekli Profesyonel Rapor Oluşturma Platformu',
            theme_color='#4e73df',
            default_report_cost=1,
            welcome_bonus_credits=5
        )
        db.session.add(settings)
    
    # Varsayılan kredi paketleri
    if CreditPackage.query.count() == 0:
        packages = [
            CreditPackage(
                name='Başlangıç Paketi',
                description='5 rapor oluşturma hakkı',
                credits=5,
                price=49.99,
                sort_order=1
            ),
            CreditPackage(
                name='Standart Paket',
                description='15 rapor oluşturma hakkı',
                credits=15,
                price=99.99,
                sort_order=2,
                badge='Popüler'
            ),
            CreditPackage(
                name='Pro Paket',
                description='50 rapor oluşturma hakkı',
                credits=50,
                price=249.99,
                sort_order=3,
                is_featured=True,
                badge='En Avantajlı'
            ),
            CreditPackage(
                name='Kurumsal Paket',
                description='200 rapor oluşturma hakkı',
                credits=200,
                price=799.99,
                sort_order=4
            )
        ]
        for package in packages:
            db.session.add(package)
    
    db.session.commit()

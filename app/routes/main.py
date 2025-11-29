from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.announcement import Announcement
from app.models.report import Report
from app.models.transaction import Transaction
from app.models.settings import Settings
from sqlalchemy import desc

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Ana sayfa"""
    settings = Settings.get_settings()
    
    # Giriş sayfası duyuruları
    announcements = Announcement.get_active_announcements('login')
    
    return render_template('main/index.html', 
                         settings=settings,
                         announcements=announcements)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Kullanıcı kontrol paneli"""
    settings = Settings.get_settings()
    
    # Dashboard duyuruları
    announcements = Announcement.get_active_announcements('dashboard')
    
    # Son raporlar
    recent_reports = Report.query.filter_by(user_id=current_user.id)\
        .order_by(desc(Report.created_at)).limit(5).all()
    
    # Son işlemler
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(desc(Transaction.created_at)).limit(5).all()
    
    # İstatistikler
    from app import db
    total_reports = Report.query.filter_by(user_id=current_user.id).count()
    total_credits_spent = db.session.query(db.func.sum(Transaction.amount))\
        .filter(Transaction.user_id == current_user.id, Transaction.transaction_type == 'usage').scalar() or 0
    
    return render_template('main/dashboard.html',
                         settings=settings,
                         announcements=announcements,
                         recent_reports=recent_reports,
                         recent_transactions=recent_transactions,
                         total_reports=total_reports,
                         total_credits_spent=total_credits_spent)

@main_bp.route('/profile')
@login_required
def profile():
    """Kullanıcı profili"""
    return render_template('main/profile.html')

@main_bp.route('/about')
def about():
    """Hakkımızda"""
    settings = Settings.get_settings()
    return render_template('main/about.html', settings=settings)

@main_bp.route('/contact')
def contact():
    """İletişim"""
    settings = Settings.get_settings()
    return render_template('main/contact.html', settings=settings)

@main_bp.route('/pricing')
def pricing():
    """Fiyatlandırma"""
    from app.models.credit_package import CreditPackage
    
    settings = Settings.get_settings()
    packages = CreditPackage.query.filter_by(is_active=True)\
        .order_by(CreditPackage.sort_order).all()
    
    return render_template('main/pricing.html', 
                         settings=settings,
                         packages=packages)

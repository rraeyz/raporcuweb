from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.report import Report
from app.models.transaction import Transaction
from app.models.credit_package import CreditPackage
from app.models.promo_code import PromoCode
from app.models.announcement import Announcement
from app.models.settings import Settings
from app.utils.decorators import admin_required
from datetime import datetime, timedelta
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin kontrol paneli"""
    # İstatistikler
    total_users = User.query.count()
    total_reports = Report.query.count()
    total_revenue = db.session.query(func.sum(Transaction.payment_amount))\
        .filter(Transaction.transaction_type == 'purchase', Transaction.status == 'completed').scalar() or 0
    
    active_users = User.query.filter_by(is_active=True).count()
    
    # Son kullanıcılar
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Son raporlar
    recent_reports = Report.query.order_by(Report.created_at.desc()).limit(5).all()
    
    # Son işlemler
    recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_reports=total_reports,
                         total_revenue=total_revenue,
                         active_users=active_users,
                         recent_users=recent_users,
                         recent_reports=recent_reports,
                         recent_transactions=recent_transactions)

# Kullanıcı Yönetimi
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Kullanıcıları listele"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.full_name.ilike(f'%{search}%')
            )
        )
    
    users = query.order_by(User.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Kullanıcı düzenle"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name', '').strip()
        user.is_active = request.form.get('is_active') == 'on'
        user.is_admin = request.form.get('is_admin') == 'on'
        
        # Kredi güncelleme
        new_credits = request.form.get('credits', type=int)
        if new_credits is not None and new_credits != user.credits:
            old_credits = user.credits
            user.credits = new_credits
            
            # Transaction oluştur
            transaction = Transaction(
                user_id=user.id,
                transaction_type='admin_adjustment',
                amount=new_credits - old_credits,
                description=f'Admin tarafından kredi güncellendi: {old_credits} -> {new_credits}',
                status='completed'
            )
            db.session.add(transaction)
        
        db.session.commit()
        flash('Kullanıcı başarıyla güncellendi.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Kullanıcıyı sil"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Kendi hesabınızı silemezsiniz.', 'danger')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash('Kullanıcı başarıyla silindi.', 'success')
    return redirect(url_for('admin.users'))

# Paket Yönetimi
@admin_bp.route('/packages')
@login_required
@admin_required
def packages():
    """Kredi paketlerini listele"""
    packages = CreditPackage.query.order_by(CreditPackage.sort_order).all()
    return render_template('admin/packages.html', packages=packages)

@admin_bp.route('/packages/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_package():
    """Yeni paket oluştur"""
    if request.method == 'POST':
        package = CreditPackage(
            name=request.form.get('name'),
            description=request.form.get('description'),
            credits=request.form.get('credits', type=int),
            price=request.form.get('price', type=float),
            is_active=request.form.get('is_active') == 'on',
            is_featured=request.form.get('is_featured') == 'on',
            badge=request.form.get('badge', '').strip() or None,
            sort_order=request.form.get('sort_order', type=int, default=0)
        )
        
        db.session.add(package)
        db.session.commit()
        
        flash('Paket başarıyla oluşturuldu.', 'success')
        return redirect(url_for('admin.packages'))
    
    return render_template('admin/create_package.html')

@admin_bp.route('/packages/<int:package_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_package(package_id):
    """Paketi düzenle"""
    package = CreditPackage.query.get_or_404(package_id)
    
    if request.method == 'POST':
        package.name = request.form.get('name')
        package.description = request.form.get('description')
        package.credits = request.form.get('credits', type=int)
        package.price = request.form.get('price', type=float)
        package.is_active = request.form.get('is_active') == 'on'
        package.is_featured = request.form.get('is_featured') == 'on'
        package.badge = request.form.get('badge', '').strip() or None
        package.sort_order = request.form.get('sort_order', type=int, default=0)
        
        db.session.commit()
        flash('Paket başarıyla güncellendi.', 'success')
        return redirect(url_for('admin.packages'))
    
    return render_template('admin/edit_package.html', package=package)

@admin_bp.route('/packages/<int:package_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_package(package_id):
    """Paketi sil"""
    package = CreditPackage.query.get_or_404(package_id)
    db.session.delete(package)
    db.session.commit()
    
    flash('Paket başarıyla silindi.', 'success')
    return redirect(url_for('admin.packages'))

# Promosyon Kodu Yönetimi
@admin_bp.route('/promo-codes')
@login_required
@admin_required
def promo_codes():
    """Promosyon kodlarını listele"""
    codes = PromoCode.query.order_by(PromoCode.created_at.desc()).all()
    return render_template('admin/promo_codes.html', codes=codes)

@admin_bp.route('/promo-codes/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_promo_code():
    """Yeni promosyon kodu oluştur"""
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        if not code:
            code = PromoCode.generate_code()
        
        promo_code = PromoCode(
            code=code,
            description=request.form.get('description'),
            discount_type=request.form.get('discount_type'),
            discount_value=request.form.get('discount_value', type=float),
            max_uses=request.form.get('max_uses', type=int) or None,
            max_uses_per_user=request.form.get('max_uses_per_user', type=int, default=1),
            min_purchase_amount=request.form.get('min_purchase_amount', type=float, default=0),
            is_active=request.form.get('is_active') == 'on',
            valid_from=datetime.utcnow(),
            valid_until=request.form.get('valid_until', type=lambda x: datetime.strptime(x, '%Y-%m-%d') if x else None)
        )
        
        db.session.add(promo_code)
        db.session.commit()
        
        flash(f'Promosyon kodu oluşturuldu: {code}', 'success')
        return redirect(url_for('admin.promo_codes'))
    
    return render_template('admin/create_promo_code.html')

@admin_bp.route('/promo-codes/<int:code_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_promo_code(code_id):
    """Promosyon kodunu sil"""
    code = PromoCode.query.get_or_404(code_id)
    db.session.delete(code)
    db.session.commit()
    
    flash('Promosyon kodu silindi.', 'success')
    return redirect(url_for('admin.promo_codes'))

# Duyuru Yönetimi
@admin_bp.route('/announcements')
@login_required
@admin_required
def announcements():
    """Duyuruları listele"""
    announcements = Announcement.query.order_by(Announcement.priority.desc(), Announcement.created_at.desc()).all()
    return render_template('admin/announcements.html', announcements=announcements)

@admin_bp.route('/announcements/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_announcement():
    """Yeni duyuru oluştur"""
    if request.method == 'POST':
        announcement = Announcement(
            title=request.form.get('title'),
            content=request.form.get('content'),
            announcement_type=request.form.get('announcement_type', 'info'),
            is_active=request.form.get('is_active') == 'on',
            show_on_dashboard=request.form.get('show_on_dashboard') == 'on',
            show_on_login=request.form.get('show_on_login') == 'on',
            priority=request.form.get('priority', type=int, default=0),
            valid_from=datetime.utcnow(),
            valid_until=request.form.get('valid_until', type=lambda x: datetime.strptime(x, '%Y-%m-%d') if x else None)
        )
        
        db.session.add(announcement)
        db.session.commit()
        
        flash('Duyuru oluşturuldu.', 'success')
        return redirect(url_for('admin.announcements'))
    
    return render_template('admin/create_announcement.html')

@admin_bp.route('/announcements/<int:announcement_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_announcement(announcement_id):
    """Duyuru düzenle"""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    if request.method == 'POST':
        announcement.title = request.form.get('title')
        announcement.content = request.form.get('content')
        announcement.announcement_type = request.form.get('announcement_type', 'info')
        announcement.is_active = request.form.get('is_active') == 'on'
        announcement.show_on_dashboard = request.form.get('show_on_dashboard') == 'on'
        announcement.show_on_login = request.form.get('show_on_login') == 'on'
        announcement.priority = request.form.get('priority', type=int, default=0)
        
        valid_until_str = request.form.get('valid_until')
        if valid_until_str:
            announcement.valid_until = datetime.strptime(valid_until_str, '%Y-%m-%d')
        
        db.session.commit()
        flash('Duyuru güncellendi.', 'success')
        return redirect(url_for('admin.announcements'))
    
    return render_template('admin/edit_announcement.html', announcement=announcement)

@admin_bp.route('/announcements/<int:announcement_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_announcement(announcement_id):
    """Duyuruyu sil"""
    announcement = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    
    flash('Duyuru silindi.', 'success')
    return redirect(url_for('admin.announcements'))

# Site Ayarları
@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Site ayarları"""
    settings = Settings.get_settings()
    
    if request.method == 'POST':
        try:
            settings.site_name = request.form.get('site_name')
            settings.site_description = request.form.get('site_description')
            settings.theme_color = request.form.get('theme_color')
            settings.contact_email = request.form.get('contact_email')
            settings.support_email = request.form.get('support_email')
            settings.phone = request.form.get('phone')
            
            # Shopier ayarları
            settings.shopier_payment_url = request.form.get('shopier_payment_url')
            
            # Kredi ayarları
            settings.default_report_cost = request.form.get('default_report_cost', type=int)
            settings.welcome_bonus_credits = request.form.get('welcome_bonus_credits', type=int)
            
            # Özellikler (checkbox'lar için 'on' kontrolü)
            settings.enable_registration = 'enable_registration' in request.form
            settings.enable_email_verification = 'enable_email_verification' in request.form
            settings.enable_password_reset = 'enable_password_reset' in request.form
            settings.maintenance_mode = 'maintenance_mode' in request.form
            
            # AI ayarları
            settings.default_ai_model = request.form.get('default_ai_model', 'openai')
            
            # AI API Keys
            openai_key = request.form.get('openai_api_key', '').strip()
            anthropic_key = request.form.get('anthropic_api_key', '').strip()
            google_key = request.form.get('google_api_key', '').strip()
            
            if openai_key:
                settings.openai_api_key = openai_key
            if anthropic_key:
                settings.anthropic_api_key = anthropic_key
            if google_key:
                settings.google_api_key = google_key
            
            db.session.commit()
            flash('Ayarlar başarıyla güncellendi.', 'success')
            return redirect(url_for('admin.settings'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ayarlar kaydedilirken hata oluştu: {str(e)}', 'danger')
    
    return render_template('admin/settings.html', settings=settings)

# Raporlar
@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Tüm raporları listele"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    reports = Report.query.order_by(Report.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/reports.html', reports=reports)

# İşlemler
@admin_bp.route('/transactions')
@login_required
@admin_required
def transactions():
    """Tüm işlemleri listele"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    transactions = Transaction.query.order_by(Transaction.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/transactions.html', transactions=transactions)

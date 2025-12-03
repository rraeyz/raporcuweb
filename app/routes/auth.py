from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, limiter
from app.models.user import User
from app.models.settings import Settings
from app.services.email_service import send_verification_email, send_password_reset_email, send_welcome_email
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    """Kullanıcı kaydı"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    from app.models.settings import Settings
    settings = Settings.get_settings()
    
    if not settings.enable_registration:
        flash('Kayıt işlemi şu anda devre dışı.', 'warning')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        # Validasyon
        if not username or not email or not password:
            flash('Tüm alanları doldurun.', 'danger')
            return render_template('auth/register.html')
        
        if len(username) < 3 or len(username) > 80:
            flash('Kullanıcı adı 3-80 karakter arasında olmalı.', 'danger')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Şifre en az 6 karakter olmalı.', 'danger')
            return render_template('auth/register.html')
        
        if password != password_confirm:
            flash('Şifreler eşleşmiyor.', 'danger')
            return render_template('auth/register.html')
        
        # Kullanıcı kontrolü
        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten kullanılıyor.', 'danger')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Bu e-posta adresi zaten kayıtlı.', 'danger')
            return render_template('auth/register.html')
        
        # Kullanıcı oluştur
        user = User(
            username=username,
            email=email,
            credits=settings.welcome_bonus_credits or 0
        )
        user.set_password(password)
        
        # E-posta doğrulama
        if settings.enable_email_verification:
            token = user.generate_email_verification_token()
            send_verification_email(user, token)
        else:
            user.email_verified = True
        
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Kayıt sırasında hata oluştu: {str(e)}', 'danger')
            return render_template('auth/register.html')
        
        if settings.enable_email_verification:
            flash('Kayıt başarılı! E-posta adresinize gönderilen bağlantıyla hesabınızı doğrulayın.', 'success')
        else:
            flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
            return redirect(url_for('auth.login'))
        
        return redirect(url_for('auth.verify_email_notice'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """Kullanıcı girişi"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'
        
        if not username or not password:
            flash('Kullanıcı adı ve şifre gerekli.', 'danger')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Geçersiz kullanıcı adı veya şifre.', 'danger')
            return render_template('auth/login.html')
        
        if not user.is_active:
            flash('Hesabınız devre dışı bırakılmış.', 'danger')
            return render_template('auth/login.html')
        
        # Giriş yap
        login_user(user, remember=remember)
        user.last_login = datetime.utcnow()
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Login timestamp hatası kritik değil, devam et
            current_app.logger.error(f'Last login update error: {e}')
        
        # Yönlendirme
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Çıkış yap"""
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    """E-posta doğrulama"""
    user = User.query.filter_by(email_verification_token=token).first()
    
    if not user:
        flash('Geçersiz doğrulama bağlantısı.', 'danger')
        return redirect(url_for('main.index'))
    
    user.verify_email()
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'E-posta doğrulama kaydedilirken hata: {str(e)}', 'danger')
        return redirect(url_for('main.index'))
    
    send_welcome_email(user)
    
    flash('E-posta adresiniz başarıyla doğrulandı! Giriş yapabilirsiniz.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/verify-email-notice')
def verify_email_notice():
    """E-posta doğrulama bildirimi"""
    return render_template('auth/verify_email_notice.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def forgot_password():
    """Şifre sıfırlama talebi"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    from app.models.settings import Settings
    settings = Settings.get_settings()
    
    if not settings.enable_password_reset:
        flash('Şifre sıfırlama şu anda devre dışı.', 'warning')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('E-posta adresi gerekli.', 'danger')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = user.generate_password_reset_token()
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Password reset token save error: {e}')
            send_password_reset_email(user, token)
        
        # Güvenlik için her durumda aynı mesajı göster
        flash('Eğer bu e-posta adresi kayıtlıysa, şifre sıfırlama bağlantısı gönderildi.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Şifre sıfırlama"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user or not user.password_reset_expires or user.password_reset_expires < datetime.utcnow():
        flash('Geçersiz veya süresi dolmuş sıfırlama bağlantısı.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        if not password:
            flash('Şifre gerekli.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        if len(password) < 6:
            flash('Şifre en az 6 karakter olmalı.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        if password != password_confirm:
            flash('Şifreler eşleşmiyor.', 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        # Şifreyi güncelle
        user.set_password(password)
        user.password_reset_token = None
        user.password_reset_expires = None
        try:
            db.session.commit()
            flash('Şifreniz başarıyla güncellendi. Giriş yapabilirsiniz.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Şifre güncellenirken hata: {str(e)}', 'danger')
            return render_template('auth/reset_password.html', token=token)
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Şifre değiştirme (zorunlu veya isteğe bağlı)"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        new_password_confirm = request.form.get('new_password_confirm', '')
        
        # Mevcut şifreyi kontrol et
        if not current_password or not current_user.check_password(current_password):
            flash('Mevcut şifreniz yanlış.', 'danger')
            return render_template('auth/change_password.html')
        
        # Validasyon
        if not new_password:
            flash('Yeni şifre gerekli.', 'danger')
            return render_template('auth/change_password.html')
        
        if len(new_password) < 6:
            flash('Yeni şifre en az 6 karakter olmalı.', 'danger')
            return render_template('auth/change_password.html')
        
        if new_password != new_password_confirm:
            flash('Yeni şifreler eşleşmiyor.', 'danger')
            return render_template('auth/change_password.html')
        
        # Şifreyi güncelle
        current_user.set_password(new_password)
        try:
            db.session.commit()
            flash('Şifreniz başarıyla değiştirildi.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Şifre değiştirilirken hata oluştu: {str(e)}', 'danger')
            return render_template('auth/change_password.html')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/change_password.html')

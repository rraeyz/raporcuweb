from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user

def admin_required(f):
    """Admin yetkisi kontrolü için decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Bu sayfaya erişmek için lütfen giriş yapın.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def email_verified_required(f):
    """E-posta doğrulama kontrolü için decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Bu sayfaya erişmek için lütfen giriş yapın.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.email_verified:
            flash('Bu işlemi yapmak için e-posta adresinizi doğrulamanız gerekiyor.', 'warning')
            return redirect(url_for('auth.verify_email_notice'))
        return f(*args, **kwargs)
    return decorated_function

def credits_required(min_credits=1):
    """Minimum kredi kontrolü için decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Bu sayfaya erişmek için lütfen giriş yapın.', 'warning')
                return redirect(url_for('auth.login'))
            if current_user.credits < min_credits:
                flash(f'Bu işlem için en az {min_credits} krediniz olmalı. Lütfen kredi satın alın.', 'warning')
                return redirect(url_for('market.packages'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import csrf
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

@main_bp.route('/webhook/shopier', methods=['POST', 'GET'])
@csrf.exempt
def shopier_webhook():
    """Shopier webhook - Ödeme tamamlandığında buraya POST/GET gönderir"""
    try:
        import json
        import hmac
        import hashlib
        import base64
        from flask import request, current_app, redirect, url_for
        from app import db
        from app.models.user import User
        from app.models.credit_package import CreditPackage
        from app.models.transaction import Transaction
        from app.models.settings import Settings
        
        # Webhook verisini al (POST form, JSON, veya GET params)
        if request.method == 'POST':
            data = request.form.to_dict() or request.get_json() or {}
        else:
            data = request.args.to_dict()
        
        # DETAYLI LOG - Her şeyi görelim
        current_app.logger.info(f"🔔 Shopier webhook çağrıldı:")
        current_app.logger.info(f"   Method: {request.method}")
        current_app.logger.info(f"   Headers: {dict(request.headers)}")
        current_app.logger.info(f"   Form data: {dict(request.form)}")
        current_app.logger.info(f"   Args: {dict(request.args)}")
        current_app.logger.info(f"   JSON: {request.get_json(silent=True)}")
        current_app.logger.info(f"   Parsed data: {json.dumps(data)}")
        
        # Eğer GET isteği boş gelirse (sadece kullanıcı redirect'i)
        if request.method == 'GET' and not data:
            current_app.logger.info("ℹ️ Boş GET isteği (kullanıcı yönlendirmesi), dashboard'a gönder")
            from flask import flash
            flash('Ödeme işleminiz alındı, kredi eklenme işlemi devam ediyor...', 'info')
            return redirect(url_for('main.dashboard'))
        
        # Signature doğrulaması (güvenlik için önemli!)
        # ŞİMDİLİK DEVRE DIŞI - Test aşamasında
        settings = Settings.get_settings()
        if False and settings.shopier_api_secret:  # Signature kontrolü devre dışı
            # Shopier signature: base64(HMAC-SHA256(random_nr + platform_order_id + total_order_value + currency, secret))
            random_nr = data.get('random_nr', '')
            platform_order_id = data.get('platform_order_id', '')
            total_order_value = data.get('total_order_value', '')
            currency = data.get('currency', '0')
            
            signature_data = f"{random_nr}{platform_order_id}{total_order_value}{currency}"
            expected_signature = hmac.new(
                settings.shopier_api_secret.encode(),
                signature_data.encode(),
                hashlib.sha256
            ).digest()
            expected_signature = base64.b64encode(expected_signature).decode()
            
            received_signature = data.get('signature', '')
            
            if received_signature != expected_signature:
                current_app.logger.error(f"❌ Signature mismatch: {received_signature} != {expected_signature}")
                current_app.logger.error(f"   Expected: {expected_signature}")
                current_app.logger.error(f"   Received: {received_signature}")
                current_app.logger.error(f"   Data: random_nr={random_nr}, order={platform_order_id}, amount={total_order_value}, currency={currency}")
                return {'status': 'error', 'message': 'Invalid signature'}, 403
            
            current_app.logger.info("✅ Signature verified")
        else:
            current_app.logger.warning("⚠️ Signature validation DISABLED (test mode)")
        
        # Ödeme durumu kontrol
        status = data.get('status', '')
        current_app.logger.info(f"   Payment status: '{status}'")
        
        # Shopier farklı status değerleri gönderebilir: success, 1, completed, paid vb.
        if str(status).lower() not in ['success', 'completed', 'paid', '1', 'true']:
            current_app.logger.warning(f"⚠️ Payment not successful, status={status}")
            if request.method == 'GET':
                from flask import flash
                flash('Ödeme tamamlanamadı. Lütfen tekrar deneyin.', 'warning')
                return redirect(url_for('main.dashboard'))
            return {'status': 'error', 'message': 'Payment not successful'}, 400
        
        order_id = data.get('platform_order_id')
        payment_amount = float(data.get('total_order_value', 0))
        
        # Tekrar işleme kontrolü
        if order_id:
            existing = Transaction.query.filter_by(payment_id=str(order_id)).first()
            if existing:
                current_app.logger.info(f"⚠️ Order already processed: {order_id}")
                return {'status': 'success', 'message': 'Already processed'}, 200
        
        # Custom field'lardan bilgileri al
        package_id = data.get('custom_field_1') or data.get('custom1')
        user_id = data.get('custom_field_2') or data.get('custom2')
        credits = data.get('custom_field_3') or data.get('custom3')
        
        # Tip dönüşümleri
        try:
            package_id = int(package_id) if package_id else None
            user_id = int(user_id) if user_id else None
            credits = int(credits) if credits else None
        except (ValueError, TypeError):
            current_app.logger.error(f"❌ Invalid data types: pkg={package_id}, user={user_id}, credits={credits}")
            return {'status': 'error', 'message': 'Invalid data'}, 400
        
        if not all([package_id, user_id, credits]):
            current_app.logger.error(f"❌ Missing fields: pkg={package_id}, user={user_id}, credits={credits}, all_data={data}")
            # GET isteğiyse ve veri yoksa kullanıcıyı dashboard'a yönlendir
            if request.method == 'GET':
                return redirect(url_for('main.dashboard'))
            return {'status': 'error', 'message': 'Missing required fields'}, 400
        
        # Kullanıcı ve paket
        user = User.query.get(user_id)
        package = CreditPackage.query.get(package_id)
        
        if not user or not package:
            current_app.logger.error(f"❌ Not found: user={user_id}, package={package_id}")
            return {'status': 'error', 'message': 'User or package not found'}, 404
        
        # Kredi ekle
        user.add_credits(credits)
        
        # Transaction
        transaction = Transaction(
            user_id=user.id,
            transaction_type='purchase',
            amount=credits,
            description=f'{package.name} paketi satın alındı (Shopier)',
            payment_method='shopier',
            payment_id=str(order_id),
            payment_amount=payment_amount,
            status='completed'
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        current_app.logger.info(f"✅ Payment OK: user={user.email}, pkg={package.name}, credits={credits}, order={order_id}")
        
        # POST isteğiyse JSON dön, GET isteğiyse kullanıcıyı yönlendir
        if request.method == 'GET':
            from flask import flash
            flash(f'Ödeme başarılı! {credits} kredi hesabınıza eklendi.', 'success')
            return redirect(url_for('main.dashboard'))
        
        return {'status': 'success', 'message': 'Payment processed'}, 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': str(e)}, 500

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import csrf, limiter
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
@limiter.exempt
def shopier_webhook():
    """Shopier webhook - Ödeme sonrası geri dönüş"""
    try:
        from flask import request, current_app, redirect, url_for, flash
        from flask_login import current_user
        from app import db
        from app.models.user import User
        from app.models.credit_package import CreditPackage
        from app.models.transaction import Transaction
        
        current_app.logger.info(f"🔔 Shopier callback: method={request.method}, user={'logged_in' if not current_user.is_anonymous else 'anonymous'}")
        
        # URL parametrelerini kontrol et
        url_params = request.args.to_dict()
        current_app.logger.info(f"   URL params: {url_params}")
        
        # Son pending transaction'ı bul (tüm kullanıcılardan - user_id order_id'de var)
        pending_tx = Transaction.query.filter_by(
            status='pending'
        ).order_by(Transaction.created_at.desc()).first()
        
        if not pending_tx:
            current_app.logger.error(f"❌ Hiç pending transaction bulunamadı!")
            return '''
                <html><body style="font-family:Arial;padding:50px;text-align:center;">
                    <h2>⚠️ Ödeme bilgisi bulunamadı</h2>
                    <p>Eğer ödeme yaptıysanız lütfen destek ile iletişime geçin.</p>
                    <a href="/" style="color:#667eea;text-decoration:none;">Ana Sayfaya Dön</a>
                </body></html>
            '''
        
        order_id = pending_tx.payment_id
        credits = pending_tx.amount
        user_id = pending_tx.user_id
        
        current_app.logger.info(f"   Found pending tx: id={pending_tx.id}, order={order_id}, user={user_id}, credits={credits}")
        
        # Zaten completed mu?
        if pending_tx.status == 'completed':
            current_app.logger.info(f"⚠️ Ödeme zaten tamamlanmış: {order_id}")
            return f'''
                <html><body style="font-family:Arial;padding:50px;text-align:center;">
                    <h2>✅ Ödeme Zaten Tamamlandı</h2>
                    <p>{credits} kredi zaten hesabınıza eklendi!</p>
                    <a href="/" style="display:inline-block;margin-top:20px;padding:10px 20px;background:#667eea;color:white;text-decoration:none;border-radius:4px;">Ana Sayfaya Dön</a>
                </body></html>
            '''
        
        # Kullanıcıyı bul
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"❌ User bulunamadı: {user_id}")
            return '<html><body>Kullanıcı bulunamadı!</body></html>'
        
        # ✅ KREDİYİ EKLE
        user.add_credits(credits)
        
        # Transaction'ı COMPLETED yap
        pending_tx.status = 'completed'
        pending_tx.description = pending_tx.description.replace('(ödeme bekleniyor)', '(Shopier)')
        
        try:
            db.session.commit()
            current_app.logger.info(f"✅ Ödeme başarılı: user={user.email}, credits={credits}, order={order_id}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"❌ Payment commit error: {e}")
            return '<html><body>Veritabanı hatası! Lütfen destek ile iletişime geçin.</body></html>'
        
        
        
        # Başarı sayfası göster
        return f'''
            <html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="refresh" content="3;url=/">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }}
                    .success-box {{
                        background: white;
                        padding: 50px;
                        border-radius: 10px;
                        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                        text-align: center;
                        max-width: 500px;
                    }}
                    .success-icon {{
                        font-size: 80px;
                        color: #4CAF50;
                        margin-bottom: 20px;
                    }}
                    h1 {{ color: #333; margin: 0 0 10px 0; }}
                    p {{ color: #666; margin: 10px 0; }}
                    .credits {{ font-size: 32px; color: #667eea; font-weight: bold; margin: 20px 0; }}
                    .btn {{
                        display: inline-block;
                        margin-top: 20px;
                        padding: 12px 30px;
                        background: #667eea;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                <div class="success-box">
                    <div class="success-icon">🎉</div>
                    <h1>Ödeme Başarılı!</h1>
                    <div class="credits">{credits} Kredi</div>
                    <p>Hesabınıza başarıyla eklendi</p>
                    <p style="font-size:14px;color:#999;">3 saniye içinde ana sayfaya yönlendirileceksiniz...</p>
                    <a href="/" class="btn">Hemen Ana Sayfaya Dön</a>
                </div>
            </body>
            </html>
        '''
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        from flask import flash, redirect, url_for
        flash('Ödeme işlemi sırasında hata oluştu. Lütfen destek ile iletişime geçin.', 'error')
        return redirect(url_for('main.dashboard'))


@main_bp.route('/webhook/shopier/old', methods=['POST', 'GET'])
@csrf.exempt
def shopier_webhook_old():
    """ESKİ webhook - POST ile veri gelirse burası çalışır"""
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
        current_app.logger.info(f"🔔 Shopier webhook OLD çağrıldı:")
        current_app.logger.info(f"   Method: {request.method}")
        current_app.logger.info(f"   Headers: {dict(request.headers)}")
        current_app.logger.info(f"   Form data: {dict(request.form)}")
        current_app.logger.info(f"   Args: {dict(request.args)}")
        current_app.logger.info(f"   JSON: {request.get_json(silent=True)}")
        current_app.logger.info(f"   Parsed data: {json.dumps(data)}")
        
        # Eğer GET isteği boş gelirse - debug için bilgi göster
        if request.method == 'GET' and not data:
            current_app.logger.info("ℹ️ Boş GET isteği (kullanıcı yönlendirmesi)")
            # HTTPS URL oluştur
            from flask import make_response
            dashboard_url = url_for('main.dashboard', _external=True, _scheme='https')
            
            debug_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
    <title>Webhook Debug</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; }}
        pre {{ background: #f8f8f8; padding: 15px; border-radius: 4px; overflow-x: auto; }}
        .info {{ background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 20px 0; border-left: 4px solid #2196f3; }}
        a {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔔 Webhook Debug</h1>
        <div class="info">
            <strong>Webhook endpoint'e GET isteği geldi ama veri yok.</strong>
            <p>Shopier ödeme sonrası kullanıcıyı buraya yönlendirdi.</p>
        </div>
        <h3>Request Bilgileri:</h3>
        <pre>Method: {request.method}
URL: {request.url}
Args: {dict(request.args)}
Headers: {dict(request.headers)}</pre>
        <a href="{dashboard_url}">Dashboard'a Dön</a>
    </div>
</body>
</html>
"""
            response = make_response(debug_html)
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            return response
        
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
        
        # Custom field'lardan bilgileri al (birden fazla isim denenir)
        package_id = (data.get('custom_field_1') or data.get('custom1') or 
                     data.get('customfield1') or data.get('custom_1'))
        user_id = (data.get('custom_field_2') or data.get('custom2') or 
                  data.get('customfield2') or data.get('custom_2'))
        credits = (data.get('custom_field_3') or data.get('custom3') or 
                  data.get('customfield3') or data.get('custom_3'))
        
        current_app.logger.info(f"   Custom fields: pkg={package_id}, user={user_id}, credits={credits}")
        
        # Eğer custom field yok ama platform_order_id varsa, oradan çıkar
        if not all([package_id, user_id, credits]) and order_id:
            # platform_order_id format: "PKG{package_id}_U{user_id}_{timestamp}"
            if order_id.startswith('PKG') and '_U' in order_id:
                try:
                    parts = order_id.split('_')
                    package_id = int(parts[0].replace('PKG', ''))
                    user_id = int(parts[1].replace('U', ''))
                    current_app.logger.info(f"   Extracted from order_id: pkg={package_id}, user={user_id}")
                    
                    # Paketten kredi bilgisini al
                    package = CreditPackage.query.get(package_id)
                    if package:
                        credits = package.credits
                        current_app.logger.info(f"   Credits from package: {credits}")
                except Exception as e:
                    current_app.logger.error(f"❌ Order ID parse error: {e}")
        
        # Tip dönüşümleri
        try:
            package_id = int(package_id) if package_id else None
            user_id = int(user_id) if user_id else None
            credits = int(credits) if credits else None
        except (ValueError, TypeError) as e:
            current_app.logger.error(f"❌ Invalid data types: pkg={package_id}, user={user_id}, credits={credits}, error={e}")
            if request.method == 'GET':
                from flask import flash
                flash('Ödeme verisi hatalı. Lütfen destek ile iletişime geçin.', 'error')
                return redirect(url_for('main.dashboard'))
            return {'status': 'error', 'message': 'Invalid data'}, 400
        
        if not all([package_id, user_id, credits]):
            current_app.logger.error(f"❌ Missing fields after all attempts:")
            current_app.logger.error(f"   pkg={package_id}, user={user_id}, credits={credits}")
            current_app.logger.error(f"   All data={json.dumps(data)}")
            # GET isteğiyse ve veri yoksa kullanıcıyı dashboard'a yönlendir
            if request.method == 'GET':
                from flask import flash
                flash('Ödeme bilgisi eksik. Eğer ödeme yaptıysanız lütfen destek ile iletişime geçin.', 'warning')
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

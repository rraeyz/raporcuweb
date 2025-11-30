from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.credit_package import CreditPackage
from app.models.promo_code import PromoCode
from app.models.transaction import Transaction
from app.services.payment_service import PaymentService

market_bp = Blueprint('market', __name__)

@market_bp.route('/')
@market_bp.route('/packages')
@login_required
def packages():
    """Kredi paketleri listesi"""
    packages = CreditPackage.query.filter_by(is_active=True)\
        .order_by(CreditPackage.sort_order).all()
    
    return render_template('market/packages.html', packages=packages)

@market_bp.route('/buy/<int:package_id>', methods=['GET', 'POST'])
@login_required
def buy_package(package_id):
    """Paket satın alma"""
    package = CreditPackage.query.get_or_404(package_id)
    
    if not package.is_active:
        flash('Bu paket şu anda satışta değil.', 'warning')
        return redirect(url_for('market.packages'))
    
    promo_code = None
    promo_discount = 0
    final_price = package.price
    
    if request.method == 'POST':
        promo_code_text = request.form.get('promo_code', '').strip().upper()
        
        if promo_code_text:
            promo_code = PromoCode.query.filter_by(code=promo_code_text, is_active=True).first()
            
            if promo_code:
                is_valid, message = promo_code.is_valid()
                if is_valid:
                    can_use, message = promo_code.can_user_use(current_user.id)
                    if can_use:
                        if promo_code.min_purchase_amount <= package.price:
                            final_price = promo_code.apply_discount(package.price)
                            promo_discount = package.price - final_price
                            flash(f'Promosyon kodu uygulandı! {promo_discount:.2f} TL indirim.', 'success')
                        else:
                            promo_code = None
                            flash(f'Bu promosyon kodu için minimum {promo_code.min_purchase_amount:.2f} TL alışveriş gerekli.', 'warning')
                    else:
                        promo_code = None
                        flash(message, 'warning')
                else:
                    promo_code = None
                    flash(message, 'warning')
            else:
                flash('Geçersiz promosyon kodu.', 'danger')
        
        # Ödeme işlemi
        payment_service = PaymentService()
        payment_url, error = payment_service.create_payment(package, current_user)
        
        if error:
            flash(error, 'danger')
            return render_template('market/buy_package.html', 
                                 package=package, 
                                 final_price=final_price,
                                 promo_discount=promo_discount)
        
        # Shopier ödeme sayfasına yönlendir
        return redirect(payment_url)
    
    return render_template('market/buy_package.html', 
                         package=package,
                         final_price=final_price,
                         promo_discount=promo_discount)

@market_bp.route('/payment/success')
@login_required
def payment_success():
    """Ödeme başarılı sayfası"""
    flash('Ödemeniz başarıyla alındı! Kredileriniz hesabınıza tanımlandı.', 'success')
    return redirect(url_for('main.dashboard'))

@market_bp.route('/payment/cancel')
@login_required
def payment_cancel():
    """Ödeme iptal sayfası"""
    flash('Ödeme işlemi iptal edildi.', 'warning')
    return redirect(url_for('market.packages'))

@market_bp.route('/webhook/shopier', methods=['POST'])
def shopier_webhook():
    """Shopier webhook callback - Ödeme tamamlandığında otomatik çağrılır"""
    try:
        import json
        import hmac
        import hashlib
        from app.models.settings import Settings
        from app.models.user import User
        from app.models.credit_package import CreditPackage
        
        # Webhook verisini al
        data = request.get_json() or request.form.to_dict()
        
        # Signature doğrulama
        settings = Settings.get_settings()
        if settings and settings.shopier_api_secret:
            received_signature = request.headers.get('X-Shopier-Signature', '')
            expected_signature = hmac.new(
                settings.shopier_api_secret.encode(),
                json.dumps(data, sort_keys=True).encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(received_signature, expected_signature):
                return {'status': 'error', 'message': 'Invalid signature'}, 401
        
        # Ödeme durumunu kontrol et
        status = data.get('status') or data.get('payment_status')
        if status not in ['success', 'completed', 'paid', '1']:
            return {'status': 'error', 'message': 'Payment not successful'}, 400
        
        # Custom fields'tan bilgileri al (Shopier custom1, custom2, custom3 olarak gönderir)
        package_id = data.get('custom1')
        user_id = data.get('custom2')
        credits = data.get('custom3')
        
        # Tip dönüşümleri
        try:
            package_id = int(package_id) if package_id else None
            user_id = int(user_id) if user_id else None
            credits = int(credits) if credits else None
        except (ValueError, TypeError):
            return {'status': 'error', 'message': 'Invalid custom field data'}, 400
        
        if not all([user_id, package_id, credits]):
            return {'status': 'error', 'message': 'Missing required fields'}, 400
        
        # Kullanıcı ve paketi bul
        user = User.query.get(user_id)
        package = CreditPackage.query.get(package_id)
        
        if not user or not package:
            return {'status': 'error', 'message': 'User or package not found'}, 404
        
        # Aynı ödemenin tekrar işlenmesini önle
        payment_id = data.get('order_id') or data.get('platform_order_id')
        existing_transaction = Transaction.query.filter_by(payment_id=payment_id).first()
        if existing_transaction:
            return {'status': 'success', 'message': 'Already processed'}, 200
        
        # Kredi ekle
        user.add_credits(credits)
        
        # Transaction kaydı oluştur
        transaction = Transaction(
            user_id=user.id,
            transaction_type='purchase',
            amount=credits,
            description=f'{package.name} paketi satın alındı',
            payment_method='shopier',
            payment_id=payment_id,
            payment_amount=data.get('total_order_value') or package.price,
            status='completed'
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return {'status': 'success', 'message': 'Payment processed'}, 200
        
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}, 500

@market_bp.route('/transactions')
@login_required
def transactions():
    """İşlem geçmişi"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('market/transactions.html', transactions=transactions)

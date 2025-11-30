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
        
        # ✅ Session'a ödeme bilgilerini kaydet (webhook için)
        from datetime import datetime
        from flask import session
        order_id = f"PKG{package.id}_U{current_user.id}_{int(datetime.utcnow().timestamp())}"
        
        session['pending_payment'] = {
            'package_id': package.id,
            'user_id': current_user.id,
            'credits': package.credits,
            'price': package.price,
            'order_id': order_id,
            'timestamp': int(datetime.utcnow().timestamp())
        }
        
        current_app.logger.info(f"💾 Payment session saved: {session['pending_payment']}")
        
        # Ödeme işlemi
        payment_service = PaymentService()
        payment_result, error = payment_service.create_payment(package, current_user)
        
        if error:
            flash(error, 'danger')
            return render_template('market/buy_package.html', 
                                 package=package, 
                                 final_price=final_price,
                                 promo_discount=promo_discount)
        
        if not payment_result:
            flash('Ödeme sistemi yapılandırılmamış', 'danger')
            return render_template('market/buy_package.html', 
                                 package=package, 
                                 final_price=final_price,
                                 promo_discount=promo_discount)
        
        # Eğer HTML form döndüyse direkt render et
        if isinstance(payment_result, str) and '<!DOCTYPE html>' in payment_result:
            from flask import Response
            return Response(payment_result, mimetype='text/html')
        
        # URL döndüyse redirect et
        return redirect(payment_result)
    
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

@market_bp.route('/payment/callback')
def shopier_callback():
    """Shopier ödeme tamamlandıktan sonra buraya yönlendirir"""
    try:
        # URL parametrelerinden bilgileri al
        package_id = request.args.get('package', type=int)
        user_id = request.args.get('user', type=int)
        
        # Shopier'den gelen ödeme durumu parametreleri
        payment_status = request.args.get('status') or request.args.get('payment_status')
        order_id = request.args.get('order_id') or request.args.get('platform_order_id')
        
        if not all([package_id, user_id]):
            flash('Geçersiz ödeme bilgileri', 'danger')
            return redirect(url_for('market.packages'))
        
        from app.models.user import User
        from app.models.credit_package import CreditPackage
        
        user = User.query.get(user_id)
        package = CreditPackage.query.get(package_id)
        
        if not user or not package:
            flash('Kullanıcı veya paket bulunamadı', 'danger')
            return redirect(url_for('market.packages'))
        
        # Ödeme başarılıysa (Shopier başarılı ödemelerde status=1 gönderir)
        if payment_status in ['1', 'success', 'completed']:
            # Aynı ödemenin tekrar işlenmesini önle
            if order_id:
                existing = Transaction.query.filter_by(payment_id=str(order_id)).first()
                if existing:
                    flash('Bu ödeme zaten işlenmiş', 'info')
                    return redirect(url_for('main.dashboard'))
            
            # Kredi ekle
            user.add_credits(package.credits)
            
            # Transaction kaydı
            transaction = Transaction(
                user_id=user.id,
                transaction_type='purchase',
                amount=package.credits,
                description=f'{package.name} paketi satın alındı',
                payment_method='shopier',
                payment_id=str(order_id) if order_id else None,
                payment_amount=package.price,
                status='completed'
            )
            db.session.add(transaction)
            db.session.commit()
            
            flash(f'Ödeme başarılı! {package.credits} kredi hesabınıza eklendi.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Ödeme başarısız veya iptal edildi', 'warning')
            return redirect(url_for('market.packages'))
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Callback error: {e}")
        flash('Ödeme işlenirken bir hata oluştu', 'danger')
        return redirect(url_for('market.packages'))

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

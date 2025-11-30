import hashlib
from flask import current_app, url_for

class PaymentService:
    """Shopier Callback-based Payment Integration"""
    
    def __init__(self):
        from app.models.settings import Settings
        settings = Settings.get_settings()
        self.payment_url_template = settings.shopier_payment_url if settings else None
    
    def create_payment(self, package, user, session):
        """
        Shopier ödeme linki oluştur - sadece tutar gönder (dijital ürün gibi)
        Paket bilgisi session'da saklanacak, webhook dönünce kullanılacak
        """
        if not self.payment_url_template:
            return None, 'Shopier ödeme linki yapılandırılmamış. Admin panelden ayarlayın.'
        
        try:
            # Session'a paket bilgisini kaydet
            session['pending_package_id'] = package.id
            session['pending_user_id'] = user.id
            session.modified = True
            
            # Shopier'a sadece ödeme linkini gönder (tutar Shopier'da tanımlı)
            # Dijital ürün gibi çalışacak
            payment_url = self.payment_url_template
            
            current_app.logger.info(f"Payment initiated: pkg={package.id}, user={user.id}, price={package.price} TL")
            return payment_url, None
            
        except Exception as e:
            current_app.logger.error(f"Payment URL error: {e}")
            return None, f'Ödeme linki oluşturma hatası: {str(e)}'
    
    def _create_legacy_payment_url(self, package, user):
        """Eski yöntem: Basit URL yönlendirme (backward compatibility)"""
        from app.models.settings import Settings
        settings = Settings.get_settings()
        
        base_url = settings.shopier_payment_url
        if not base_url:
            return None, 'Ödeme sistemi yapılandırılmamış.'
        
        payment_url = f"{base_url}?package_id={package.id}&user_id={user.id}&amount={package.price}"
        return payment_url, None
    
    def verify_webhook(self, data, signature):
        """Shopier webhook imzasını doğrula"""
        if not self.api_secret:
            return False
        
        # HMAC ile imza doğrulama
        expected_signature = hmac.new(
            self.api_secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def process_payment_callback(self, payment_data):
        """Ödeme callback'ini işle"""
        try:
            from app import db
            from app.models.user import User
            from app.models.transaction import Transaction
            from app.models.credit_package import CreditPackage
            
            # Ödeme bilgilerini al
            user_id = payment_data.get('user_id')
            package_id = payment_data.get('package_id')
            payment_id = payment_data.get('payment_id')
            status = payment_data.get('status')
            
            if status != 'success':
                return False, 'Ödeme başarısız.'
            
            # Kullanıcı ve paketi bul
            user = User.query.get(user_id)
            package = CreditPackage.query.get(package_id)
            
            if not user or not package:
                return False, 'Kullanıcı veya paket bulunamadı.'
            
            # Kredi ekle
            user.add_credits(package.credits)
            
            # Transaction oluştur
            transaction = Transaction(
                user_id=user.id,
                transaction_type='purchase',
                amount=package.credits,
                description=f'{package.name} paketi satın alındı',
                payment_method='shopier',
                payment_id=payment_id,
                payment_amount=package.price,
                status='completed'
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return True, 'Ödeme başarıyla işlendi.'
            
        except Exception as e:
            db.session.rollback()
            return False, f'Ödeme işleme hatası: {str(e)}'

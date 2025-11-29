import requests
import hmac
import hashlib
from flask import current_app

class PaymentService:
    """Shopier ödeme entegrasyonu"""
    
    def __init__(self):
        self.api_key = current_app.config.get('SHOPIER_API_KEY')
        self.api_secret = current_app.config.get('SHOPIER_API_SECRET')
    
    def create_payment_url(self, package, user):
        """Ödeme URL'i oluştur (Shopier'e yönlendirme)"""
        from app.models.settings import Settings
        
        settings = Settings.get_settings()
        
        # Temel ödeme URL'i admin panelden ayarlanmış
        base_url = settings.shopier_payment_url
        
        if not base_url:
            return None, 'Ödeme sistemi yapılandırılmamış.'
        
        # URL parametrelerini ekle
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

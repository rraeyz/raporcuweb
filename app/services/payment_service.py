import requests
import hmac
import hashlib
import json
import base64
from flask import current_app, url_for

class PaymentService:
    """Shopier REST API v2 entegrasyonu"""
    
    def __init__(self):
        from app.models.settings import Settings
        settings = Settings.get_settings()
        self.api_key = settings.shopier_api_key if settings else None
        self.api_secret = settings.shopier_api_secret if settings else None
        self.base_url = 'https://www.shopier.com/api/v2'
    
    def create_payment(self, package, user):
        """Shopier API - GET method with URL parameters (Official Method)"""
        if not self.api_key or not self.api_secret:
            return self._create_legacy_payment_url(package, user)
        
        try:
            import time
            from urllib.parse import urlencode
            
            # Random number (benzersiz işlem için)
            timestamp = int(time.time())
            random_nr = hashlib.md5(f"{timestamp}{user.id}{package.id}".encode()).hexdigest()[:10]
            
            # Signature hesaplama (Shopier resmi formatı)
            # Format: sha256(API_key + random_nr + total_order_value + API_secret)
            signature_string = f"{self.api_key}{random_nr}{package.price}{self.api_secret}"
            signature = hashlib.sha256(signature_string.encode('utf-8')).hexdigest()
            
            # Shopier API parametreleri (GET method)
            params = {
                'API_key': self.api_key,
                'website_index': 1,
                'platform_order_id': f"ORD{timestamp}{user.id}",
                'product_name': package.name,
                'product_type': 3,  # 3 = Dijital ürün
                'buyer_name': user.full_name or user.username,
                'buyer_phone': '5555555555',
                'buyer_account_age': 0,
                'buyer_email': user.email,
                'buyer_id_nr': user.id,
                'total_order_value': float(package.price),
                'currency': 'TL',
                'platform': 'RaporcuWeb',
                'is_in_frame': 0,
                'current_language': 'tr',
                'modul_version': '1.0.0',
                'random_nr': random_nr,
                'signature': signature,
                # Custom field'lar (webhook'ta kullanacağız)
                'custom_field_1': str(package.id),
                'custom_field_2': str(user.id), 
                'custom_field_3': str(package.credits)
            }
            
            # Shopier ödeme URL'i oluştur (GET method)
            payment_url = f"https://www.shopier.com/ShowProductNew/api_pay.php?{urlencode(params)}"
            
            current_app.logger.info(f"Shopier payment URL created: random_nr={random_nr}")
            return payment_url, None
                
        except Exception as e:
            current_app.logger.error(f"Shopier payment error: {e}")
            return None, f'Ödeme oluşturma hatası: {str(e)}'
    
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

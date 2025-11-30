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
        """Shopier Quick Pay API - IFrame/Direct Payment"""
        if not self.api_key or not self.api_secret:
            return self._create_legacy_payment_url(package, user)
        
        try:
            import time
            
            # Benzersiz sipariş ID
            timestamp = int(time.time())
            random_suffix = hashlib.md5(f"{user.id}{package.id}{timestamp}".encode()).hexdigest()[:6]
            order_id = f"{timestamp}{random_suffix}"
            
            # Shopier Quick Pay - JSON payload
            payload = {
                "api_key": self.api_key,
                "api_secret": self.api_secret,
                "random_nr": random_suffix,
                "order_id": order_id,
                "order_name": package.name,
                "order_price": float(package.price),
                "buyer": {
                    "id": user.id,
                    "name": user.full_name or user.username,
                    "email": user.email,
                    "phone": "5555555555"
                },
                "callback_url": url_for('market.shopier_webhook', _external=True),
                "website_index": 1,
                "lang": "tr",
                # Ekstra veri
                "buyer_account_age": 0,
                "product_type": 3,  # Dijital
                "custom_fields": {
                    "package_id": package.id,
                    "user_id": user.id,
                    "credits": package.credits
                }
            }
            
            # API isteği
            response = requests.post(
                'https://www.shopier.com/api/v2/payment',
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=15
            )
            
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                payment_url = result.get('payment_url') or result.get('url') or result.get('redirect_url')
                
                if payment_url:
                    current_app.logger.info(f"Shopier payment created: {order_id}")
                    return payment_url, None
                else:
                    error_msg = result.get('message', 'Payment URL not returned')
                    current_app.logger.error(f"Shopier error: {error_msg}")
                    return None, f'Shopier: {error_msg}'
            else:
                error_detail = response.text[:200]
                current_app.logger.error(f"Shopier HTTP {response.status_code}: {error_detail}")
                return None, f'Shopier API hatası: {response.status_code}'
                
        except requests.exceptions.Timeout:
            return None, 'Shopier bağlantı zaman aşımı'
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Shopier request error: {e}")
            return None, f'Bağlantı hatası: {str(e)}'
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

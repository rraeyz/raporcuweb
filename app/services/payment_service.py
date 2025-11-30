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
        """Shopier ile ödeme - URL parametreli yöntem (Shopier Button API)"""
        if not self.api_key or not self.api_secret:
            # Fallback: Eski yöntem (basit yönlendirme)
            return self._create_legacy_payment_url(package, user)
        
        try:
            # Shopier Button API kullanıyoruz
            # Webhook callback URL
            callback_url = url_for('market.shopier_webhook', _external=True)
            success_url = url_for('market.payment_success', _external=True)
            cancel_url = url_for('market.payment_cancel', _external=True)
            
            # Platform order ID (benzersiz olmalı)
            platform_order_id = f"PKG{package.id}U{user.id}T{int(hashlib.md5(f'{user.id}{package.id}'.encode()).hexdigest()[:8], 16)}"
            
            # Shopier ödeme URL'i oluştur (Shopier Button Link yöntemi)
            # Not: Shopier'de API Key ile doğrudan payment URL oluşturma şu şekilde
            payment_url = f"https://www.shopier.com/ShowProductNew/api_pay.php"
            
            # URL parametreleri
            params = {
                'API_key': self.api_key,
                'website_index': '1',  # Shopier paneldeki site index
                'platform_order_id': platform_order_id,
                'product_name': package.name,
                'product_type': '3',  # Dijital ürün
                'buyer_name': user.full_name or user.username,
                'buyer_phone': '5555555555',
                'buyer_email': user.email,
                'total_order_value': str(package.price),
                'currency': 'TL',
                'callback_url': callback_url,
                # Custom data için
                'custom1': str(package.id),
                'custom2': str(user.id),
                'custom3': str(package.credits)
            }
            
            # Signature oluştur (API Key + Order ID + Total + API Secret)
            signature_string = f"{self.api_key}{platform_order_id}{package.price}{self.api_secret}"
            signature = hashlib.sha256(signature_string.encode('utf-8')).hexdigest()
            params['signature'] = signature
            
            # URL parametrelerini ekle
            from urllib.parse import urlencode
            full_payment_url = f"{payment_url}?{urlencode(params)}"
            
            return full_payment_url, None
                
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

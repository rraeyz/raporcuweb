import hashlib
import hmac
import base64
import random
from datetime import datetime
from flask import current_app, url_for, render_template_string

class PaymentService:
    """Shopier API v4 Payment Integration"""
    
    def __init__(self):
        from app.models.settings import Settings
        settings = Settings.get_settings()
        self.api_key = settings.shopier_api_key if settings else None
        self.api_secret = settings.shopier_api_secret if settings else None
        self.payment_url_template = settings.shopier_payment_url if settings else None
    
    def create_payment(self, package, user):
        """
        Shopier API v4 ile ödeme formu oluştur
        """
        # Eğer API key/secret varsa API v4 kullan
        if self.api_key and self.api_secret:
            return self._create_api_v4_form(package, user)
        
        # Yoksa eski yöntem (URL parametreli)
        elif self.payment_url_template:
            return self._create_simple_payment_url(package, user)
        
        else:
            return None, 'Shopier API key/secret veya ödeme linki yapılandırılmamış.'
    
    def _create_api_v4_form(self, package, user):
        """
        Shopier API v4 - Otomatik submit eden POST form oluştur
        """
        try:
            # Random number (güvenlik için)
            random_number = random.randint(1000000, 9999999)
            
            # Platform order ID (unique)
            platform_order_id = f"PKG{package.id}_U{user.id}_{int(datetime.utcnow().timestamp())}"
            
            # Kullanıcı hesap yaşı (gün olarak)
            account_created = user.created_at or datetime.utcnow()
            buyer_account_age = (datetime.utcnow() - account_created).days
            
            # İsim-soyisim ayırma (güvenli)
            full_name = user.full_name or user.username or 'Kullanıcı'
            name_parts = full_name.split() if full_name else ['Kullanıcı']
            buyer_name = name_parts[0] if name_parts else 'Kullanıcı'
            buyer_surname = ' '.join(name_parts[1:]) if len(name_parts) > 1 else 'Kullanıcı'
            
            # Webhook URL (absolute URL)
            with current_app.app_context():
                webhook_url = url_for('main.shopier_webhook', _external=True)
            
            # Form parametreleri
            args = {
                'API_key': self.api_key,
                'website_index': 1,  # 1: Kendi siteniz
                'platform_order_id': platform_order_id,
                'product_name': f"{package.name} - {package.credits} Kredi",
                'product_type': 1,  # 1: Dijital ürün
                'buyer_name': buyer_name,
                'buyer_surname': buyer_surname,
                'buyer_email': user.email,
                'buyer_account_age': buyer_account_age,
                'buyer_id_nr': 0,
                'buyer_phone': '0000000000',  # Zorunlu alan
                'billing_address': 'Türkiye',
                'billing_city': 'İstanbul',
                'billing_country': 'TR',
                'billing_postcode': '',
                'shipping_address': 'Türkiye',
                'shipping_city': 'İstanbul',
                'shipping_country': 'TR',
                'shipping_postcode': '',
                'total_order_value': str(package.price),
                'currency': '0',  # 0: TL
                'platform': 0,
                'is_in_frame': 1,
                'current_language': '0',  # 0: Türkçe
                'modul_version': '1.0.4',
                'random_nr': random_number,
                'callback_url': webhook_url,  # ✅ Webhook URL eklendi!
                # Custom fields - webhook'ta kullanılacak
                'custom_field_1': package.id,
                'custom_field_2': user.id,
                'custom_field_3': package.credits
            }
            
            # Signature oluştur: HMAC-SHA256(random_nr + platform_order_id + total_order_value + currency)
            signature_data = f"{args['random_nr']}{args['platform_order_id']}{args['total_order_value']}{args['currency']}"
            signature = hmac.new(
                self.api_secret.encode(),
                signature_data.encode(),
                hashlib.sha256
            ).digest()
            signature = base64.b64encode(signature).decode()
            args['signature'] = signature
            
            # Otomatik submit eden HTML form
            form_html = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Güvenli Ödeme Sayfasına Yönlendiriliyorsunuz...</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .loader {
            text-align: center;
            color: white;
        }
        .spinner {
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="loader">
        <div class="spinner"></div>
        <h2>Güvenli Ödeme Sayfasına Yönlendiriliyorsunuz...</h2>
        <p>Lütfen bekleyin...</p>
    </div>
    <form action="https://www.shopier.com/ShowProduct/api_pay4.php" method="post" id="shopier_payment_form">
'''
            # Hidden input'ları ekle
            for key, value in args.items():
                form_html += f'        <input type="hidden" name="{key}" value="{value}">\n'
            
            form_html += '''    </form>
    <script>
        document.getElementById("shopier_payment_form").submit();
    </script>
</body>
</html>'''
            
            current_app.logger.info(f"Shopier API v4 payment form created: order={platform_order_id}, user={user.email}, amount={package.price} TL")
            
            # HTML form'u döndür (render edilecek)
            return form_html, None
            
        except Exception as e:
            current_app.logger.error(f"Shopier API v4 error: {e}")
            return None, f'Ödeme formu oluşturma hatası: {str(e)}'
    
    def _create_simple_payment_url(self, package, user):
        """
        Basit URL yöntemi (backward compatibility)
        """
        try:
            separator = '&' if '?' in self.payment_url_template else '?'
            payment_url = f"{self.payment_url_template}{separator}custom_field_1={package.id}&custom_field_2={user.id}&custom_field_3={package.credits}"
            
            current_app.logger.info(f"Simple payment URL: pkg={package.id}, user={user.id}")
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

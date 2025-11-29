from app import db
from datetime import datetime
import secrets

class PromoCode(db.Model):
    __tablename__ = 'promo_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Kod bilgileri
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255))
    
    # İndirim bilgileri
    discount_type = db.Column(db.String(20), nullable=False)  # percentage, fixed, bonus_credits
    discount_value = db.Column(db.Float, nullable=False)
    
    # Kullanım limitleri
    max_uses = db.Column(db.Integer)  # None ise sınırsız
    current_uses = db.Column(db.Integer, default=0, nullable=False)
    
    # Kullanıcı başına limit
    max_uses_per_user = db.Column(db.Integer, default=1)
    
    # Geçerlilik tarihleri
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    
    # Minimum alışveriş tutarı
    min_purchase_amount = db.Column(db.Float, default=0)
    
    # Durum
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Tarih
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def generate_code(length=8):
        """Rastgele promosyon kodu oluştur"""
        return secrets.token_urlsafe(length)[:length].upper()
    
    def is_valid(self):
        """Promosyon kodunun geçerli olup olmadığını kontrol et"""
        if not self.is_active:
            return False, "Promosyon kodu aktif değil."
        
        now = datetime.utcnow()
        if self.valid_from and self.valid_from > now:
            return False, "Promosyon kodu henüz geçerli değil."
        
        if self.valid_until and self.valid_until < now:
            return False, "Promosyon kodunun süresi dolmuş."
        
        if self.max_uses and self.current_uses >= self.max_uses:
            return False, "Promosyon kodu kullanım limitine ulaşmış."
        
        return True, "Geçerli"
    
    def can_user_use(self, user_id):
        """Kullanıcının bu kodu kullanıp kullanamayacağını kontrol et"""
        if self.max_uses_per_user:
            from app.models.transaction import Transaction
            user_usage_count = Transaction.query.filter_by(
                user_id=user_id,
                promo_code_id=self.id
            ).count()
            
            if user_usage_count >= self.max_uses_per_user:
                return False, "Bu promosyon kodunu zaten kullandınız."
        
        return True, "Kullanabilir"
    
    def apply_discount(self, amount):
        """İndirimi uygula ve sonuç tutarı döndür"""
        if self.discount_type == 'percentage':
            discount = amount * (self.discount_value / 100)
            return max(0, amount - discount)
        elif self.discount_type == 'fixed':
            return max(0, amount - self.discount_value)
        elif self.discount_type == 'bonus_credits':
            return amount  # Bonus krediler işlemde ayrıca eklenir
        return amount
    
    def __repr__(self):
        return f'<PromoCode {self.code}>'

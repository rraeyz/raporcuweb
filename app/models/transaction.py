from app import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # İşlem bilgileri
    transaction_type = db.Column(db.String(20), nullable=False)  # purchase, usage, refund, admin_adjustment
    amount = db.Column(db.Integer, nullable=False)  # Kredi miktarı
    description = db.Column(db.String(255))
    
    # Ödeme bilgileri (satın alma işlemleri için)
    payment_method = db.Column(db.String(50))  # shopier, admin, promo_code
    payment_id = db.Column(db.String(100))  # Shopier transaction ID
    payment_amount = db.Column(db.Float)  # TL cinsinden ödeme tutarı
    
    # Promosyon kodu (eğer kullanıldıysa)
    promo_code_id = db.Column(db.Integer, db.ForeignKey('promo_codes.id'))
    
    # İlişkili rapor (usage için)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'))
    
    # Durum
    status = db.Column(db.String(20), default='completed')  # pending, completed, failed, refunded
    
    # Tarih
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # İlişkiler
    report = db.relationship('Report', backref='transaction', foreign_keys=[report_id])
    promo_code = db.relationship('PromoCode', backref='transactions', foreign_keys=[promo_code_id])
    
    def __repr__(self):
        return f'<Transaction {self.id} - {self.transaction_type}>'
    
    def to_dict(self):
        """Model'i dictionary'e çevir"""
        return {
            'id': self.id,
            'type': self.transaction_type,
            'amount': self.amount,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

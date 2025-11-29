from app import db
from datetime import datetime

class CreditPackage(db.Model):
    __tablename__ = 'credit_packages'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Paket bilgileri
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    credits = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # TL cinsinden
    
    # Görünürlük
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Sıralama ve öne çıkarma
    sort_order = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    
    # Badge/Etiket
    badge = db.Column(db.String(50))  # Örn: "En Popüler", "En Avantajlı"
    
    # Tarih
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CreditPackage {self.name}>'
    
    def to_dict(self):
        """Model'i dictionary'e çevir"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'credits': self.credits,
            'price': self.price,
            'badge': self.badge,
            'is_featured': self.is_featured
        }

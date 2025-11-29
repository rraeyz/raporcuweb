from app import db
from datetime import datetime

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Rapor bilgileri
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    prompt = db.Column(db.Text)  # Kullanıcının girdiği prompt
    
    # Format ve durum
    format_type = db.Column(db.String(20), default='markdown')  # markdown, html, pdf
    status = db.Column(db.String(20), default='processing')  # processing, completed, failed
    
    # Maliyet
    credits_used = db.Column(db.Integer, default=1, nullable=False)
    
    # Dosya bilgileri
    file_path = db.Column(db.String(255))  # PDF dosyasının yolu
    file_size = db.Column(db.Integer)  # Dosya boyutu (bytes)
    
    # AI Model bilgisi
    ai_model = db.Column(db.String(50))  # openai, anthropic, google
    
    # Tarih bilgileri
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Report {self.title}>'
    
    def to_dict(self):
        """Model'i dictionary'e çevir"""
        return {
            'id': self.id,
            'title': self.title,
            'status': self.status,
            'credits_used': self.credits_used,
            'ai_model': self.ai_model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'file_path': self.file_path
        }

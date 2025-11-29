from app import db
from datetime import datetime

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Duyuru bilgileri
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Görünürlük
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Tip ve stil
    announcement_type = db.Column(db.String(20), default='info')  # info, warning, success, danger
    show_on_dashboard = db.Column(db.Boolean, default=True)
    show_on_login = db.Column(db.Boolean, default=False)
    
    # Öncelik
    priority = db.Column(db.Integer, default=0)  # Yüksek öncelik üstte gösterilir
    
    # Geçerlilik
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    
    # Tarih
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_valid(self):
        """Duyurunun geçerli olup olmadığını kontrol et"""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        if self.valid_from and self.valid_from > now:
            return False
        
        if self.valid_until and self.valid_until < now:
            return False
        
        return True
    
    @staticmethod
    def get_active_announcements(location='dashboard'):
        """Aktif duyuruları getir"""
        query = Announcement.query.filter_by(is_active=True)
        
        if location == 'dashboard':
            query = query.filter_by(show_on_dashboard=True)
        elif location == 'login':
            query = query.filter_by(show_on_login=True)
        
        now = datetime.utcnow()
        announcements = query.filter(
            db.or_(
                Announcement.valid_from.is_(None),
                Announcement.valid_from <= now
            ),
            db.or_(
                Announcement.valid_until.is_(None),
                Announcement.valid_until >= now
            )
        ).order_by(Announcement.priority.desc(), Announcement.created_at.desc()).all()
        
        return announcements
    
    def __repr__(self):
        return f'<Announcement {self.title}>'

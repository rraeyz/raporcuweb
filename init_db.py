#!/usr/bin/env python3
"""
Database initialization script
Tüm tabloları oluşturur ve initial data'yı ekler
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from app import create_app, db
from app.models.user import User
from app.models.credit_package import CreditPackage
from app.models.settings import Settings
from werkzeug.security import generate_password_hash

def init_database():
    """Veritabanını initialize et"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Veritabanı başlatılıyor...")
        
        # Tüm tabloları oluştur
        db.create_all()
        print("✅ Tablolar oluşturuldu")
        
        # Settings oluştur
        settings = Settings.query.first()
        if not settings:
            settings = Settings(
                site_name='RaporcuAI',
                site_description='Yapay zeka destekli rapor oluşturma platformu',
                theme_color='#4e73df',
                default_report_cost=1,
                welcome_bonus_credits=2,
                enable_registration=True,
                enable_email_verification=False,  # İlk kurulumda kapalı
                default_ai_model='openai'
            )
            db.session.add(settings)
            print("✅ Settings oluşturuldu")
        
        # Admin kullanıcı oluştur
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            import secrets
            # Rastgele güçlü şifre oluştur (16 karakter, URL-safe)
            random_password = secrets.token_urlsafe(16)
            
            admin = User(
                username='admin',
                email='admin@raporcuai.com',
                full_name='Admin User',
                is_admin=True,
                is_active=True,
                email_verified=True,
                credits=100
            )
            admin.set_password(random_password)
            db.session.add(admin)
            
            print("\n" + "="*60)
            print("🔑 ADMIN KULLANICI OLUŞTURULDU")
            print("="*60)
            print(f"   Kullanıcı Adı: admin")
            print(f"   Şifre: {random_password}")
            print("="*60)
            print("⚠️  BU ŞİFREYİ GÜVENLİ BİR YERE KAYDIN!")
            print("⚠️  İlk girişte şifrenizi değiştirmeniz istenecektir.")
            print("="*60 + "\n")
        
        # Kredi paketleri oluştur
        if CreditPackage.query.count() == 0:
            packages = [
                CreditPackage(
                    name='Başlangıç Paketi',
                    description='5 rapor hazırlama kredisi',
                    credits=5,
                    price=49.90,
                    sort_order=1,
                    is_featured=False
                ),
                CreditPackage(
                    name='Standart Paket',
                    description='15 rapor hazırlama kredisi',
                    credits=15,
                    price=129.90,
                    sort_order=2,
                    is_featured=True,
                    badge='En Popüler'
                ),
                CreditPackage(
                    name='Premium Paket',
                    description='30 rapor hazırlama kredisi',
                    credits=30,
                    price=229.90,
                    sort_order=3,
                    is_featured=False,
                    badge='En Avantajlı'
                ),
                CreditPackage(
                    name='Kurumsal Paket',
                    description='100 rapor hazırlama kredisi',
                    credits=100,
                    price=699.90,
                    sort_order=4,
                    is_featured=False
                )
            ]
            
            for package in packages:
                db.session.add(package)
            
            print("✅ Kredi paketleri oluşturuldu")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("✅ VERİTABANI HAZIR!")
        print("=" * 60)
        print("\n📦 Varsayılan Paketler:")
        for pkg in CreditPackage.query.order_by(CreditPackage.sort_order).all():
            print(f"   • {pkg.name}: {pkg.credits} kredi - {pkg.price} TL")
        print("\n" + "=" * 60)

if __name__ == '__main__':
    init_database()

#!/usr/bin/env python3
"""
Database integrity checker ve backup script
"""

import os
import sys
from datetime import datetime

# Flask app'i import et
sys.path.insert(0, os.path.dirname(__file__))
from app import create_app, db
from app.models.user import User
from app.models.credit_package import CreditPackage
from app.models.transaction import Transaction
from app.models.report import Report
from app.models.promo_code import PromoCode
from app.models.announcement import Announcement
from app.models.settings import Settings

def check_database_structure():
    """Veritabanı yapısını kontrol et"""
    print("=" * 60)
    print("📊 VERİTABANI YAPISI KONTROLÜ")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        # Database engine bilgisi
        print(f"\n🔧 Database Engine: {db.engine.url}")
        print(f"🔧 Database Name: {db.engine.url.database}")
        
        # Tabloları kontrol et
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n📋 Toplam {len(tables)} tablo bulundu:\n")
        
        expected_tables = [
            'users',
            'reports', 
            'transactions',
            'credit_packages',
            'promo_codes',
            'announcements',
            'settings',
            'alembic_version'  # Migration tracking
        ]
        
        # Tablo kontrolü
        for table in expected_tables:
            if table in tables:
                columns = inspector.get_columns(table)
                indexes = inspector.get_indexes(table)
                foreign_keys = inspector.get_foreign_keys(table)
                
                print(f"✅ {table}")
                print(f"   └─ {len(columns)} kolon, {len(indexes)} index, {len(foreign_keys)} foreign key")
            else:
                print(f"❌ {table} - EKSIK!")
        
        # Eksik tablolar
        missing = set(expected_tables) - set(tables)
        if missing:
            print(f"\n⚠️  Eksik tablolar: {', '.join(missing)}")
        
        # Fazla tablolar
        extra = set(tables) - set(expected_tables)
        if extra:
            print(f"\n📌 Ekstra tablolar: {', '.join(extra)}")
        
        return tables

def check_data_integrity():
    """Veri bütünlüğünü kontrol et"""
    print("\n" + "=" * 60)
    print("🔍 VERİ BÜTÜNLÜĞÜ KONTROLÜ")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        issues = []
        
        # Users kontrolü
        users_count = User.query.count()
        print(f"\n👥 Users: {users_count}")
        
        # Orphan reports kontrol (kullanıcısı olmayan raporlar)
        orphan_reports = Report.query.filter(
            ~Report.user_id.in_(db.session.query(User.id))
        ).count()
        if orphan_reports > 0:
            print(f"   ⚠️  {orphan_reports} rapor kullanıcısız!")
            issues.append(f"Orphan reports: {orphan_reports}")
        
        # Reports kontrolü
        reports_count = Report.query.count()
        completed_reports = Report.query.filter_by(status='completed').count()
        processing_reports = Report.query.filter_by(status='processing').count()
        failed_reports = Report.query.filter_by(status='failed').count()
        
        print(f"📄 Reports: {reports_count} (✅ {completed_reports}, ⏳ {processing_reports}, ❌ {failed_reports})")
        
        # Transactions kontrolü
        transactions_count = Transaction.query.count()
        purchase_count = Transaction.query.filter_by(transaction_type='purchase').count()
        usage_count = Transaction.query.filter_by(transaction_type='usage').count()
        
        print(f"💰 Transactions: {transactions_count} (🛒 {purchase_count}, 📊 {usage_count})")
        
        # Orphan transactions
        orphan_transactions = Transaction.query.filter(
            ~Transaction.user_id.in_(db.session.query(User.id))
        ).count()
        if orphan_transactions > 0:
            print(f"   ⚠️  {orphan_transactions} transaction kullanıcısız!")
            issues.append(f"Orphan transactions: {orphan_transactions}")
        
        # Credit Packages kontrolü
        packages_count = CreditPackage.query.count()
        active_packages = CreditPackage.query.filter_by(is_active=True).count()
        print(f"📦 Credit Packages: {packages_count} (✅ {active_packages} aktif)")
        
        if active_packages == 0:
            print(f"   ⚠️  Hiç aktif paket yok!")
            issues.append("No active credit packages")
        
        # Promo Codes kontrolü
        promo_codes_count = PromoCode.query.count()
        active_promo = PromoCode.query.filter_by(is_active=True).count()
        print(f"🎟️  Promo Codes: {promo_codes_count} (✅ {active_promo} aktif)")
        
        # Announcements kontrolü
        announcements_count = Announcement.query.count()
        active_announcements = Announcement.query.filter_by(is_active=True).count()
        print(f"📢 Announcements: {announcements_count} (✅ {active_announcements} aktif)")
        
        # Settings kontrolü
        settings = Settings.query.first()
        if not settings:
            print(f"⚠️  Settings tablosu boş!")
            issues.append("Settings table empty")
        else:
            print(f"⚙️  Settings: ✅")
            print(f"   └─ Shopier URL: {'✅' if settings.shopier_payment_url else '❌'}")
            print(f"   └─ Default AI Model: {settings.default_ai_model}")
            print(f"   └─ Report Cost: {settings.default_report_cost} kredi")
        
        # Kullanıcı kredileri kontrolü
        total_credits = db.session.query(db.func.sum(User.credits)).scalar() or 0
        print(f"\n💎 Toplam Sistem Kredisi: {total_credits}")
        
        # Transaction toplamı ile karşılaştır
        purchase_credits = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter_by(transaction_type='purchase').scalar() or 0
        
        usage_credits = db.session.query(
            db.func.sum(Transaction.amount)
        ).filter_by(transaction_type='usage').scalar() or 0
        
        expected_credits = purchase_credits - usage_credits
        
        print(f"💰 Alınan Kredi: {purchase_credits}")
        print(f"📊 Kullanılan Kredi: {usage_credits}")
        print(f"🔢 Beklenen Kredi: {expected_credits}")
        
        if total_credits != expected_credits:
            print(f"⚠️  Kredi uyuşmazlığı: {total_credits} != {expected_credits}")
            issues.append(f"Credit mismatch: {total_credits} vs {expected_credits}")
        
        print("\n" + "=" * 60)
        if issues:
            print(f"❌ {len(issues)} SORUN BULUNDU:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("✅ VERİTABANI SAĞLIKLI")
        print("=" * 60)
        
        return issues

def generate_backup_sql():
    """PostgreSQL backup komutu oluştur"""
    print("\n" + "=" * 60)
    print("💾 BACKUP KOMUTLARI")
    print("=" * 60)
    
    print("""
Veritabanı yedeği almak için:

1. PostgreSQL dump (sunucuda):
   pg_dump -U raporcuweb -d raporcuweb -F c -f backup_$(date +%Y%m%d_%H%M%S).dump

2. Sadece data (INSERT komutları):
   pg_dump -U raporcuweb -d raporcuweb --data-only -f data_backup.sql

3. Sadece yapı (CREATE TABLE komutları):
   pg_dump -U raporcuweb -d raporcuweb --schema-only -f schema_backup.sql

4. Docker üzerinden:
   docker-compose exec postgres pg_dump -U raporcuweb raporcuweb > backup.sql

5. Geri yükleme:
   pg_restore -U raporcuweb -d raporcuweb_new backup.dump
   
   veya
   
   psql -U raporcuweb -d raporcuweb_new < backup.sql

6. Başka sunucuya taşıma:
   # Eski sunucuda
   pg_dump -U raporcuweb -d raporcuweb -F c -f raporcuweb_backup.dump
   
   # Yeni sunucuda (önce database oluştur)
   createdb -U postgres raporcuweb
   pg_restore -U raporcuweb -d raporcuweb raporcuweb_backup.dump
""")

def check_indexes():
    """Index kontrolü"""
    print("\n" + "=" * 60)
    print("🔎 INDEX KONTROLÜ")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        critical_indexes = {
            'users': ['username', 'email'],
            'reports': ['user_id', 'created_at'],
            'transactions': ['user_id', 'created_at'],
            'promo_codes': ['code']
        }
        
        for table, expected_indexed_columns in critical_indexes.items():
            indexes = inspector.get_indexes(table)
            indexed_columns = set()
            for idx in indexes:
                indexed_columns.update(idx['column_names'])
            
            print(f"\n📋 {table}:")
            for col in expected_indexed_columns:
                if col in indexed_columns:
                    print(f"   ✅ {col}")
                else:
                    print(f"   ❌ {col} - INDEX EKSIK!")

if __name__ == '__main__':
    try:
        check_database_structure()
        check_data_integrity()
        check_indexes()
        generate_backup_sql()
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()

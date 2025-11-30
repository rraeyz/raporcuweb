#!/usr/bin/env python3
"""
Veritabanı Troubleshooting Script
Yaygın sorunları tespit edip düzeltir
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from app import create_app, db
from app.models.user import User
from app.models.credit_package import CreditPackage
from app.models.transaction import Transaction
from app.models.report import Report
from app.models.settings import Settings
from sqlalchemy import text

def fix_orphan_records():
    """Orphan kayıtları temizle"""
    print("🔧 Orphan kayıtlar temizleniyor...")
    
    app = create_app()
    with app.app_context():
        # Kullanıcısı olmayan raporlar
        orphan_reports = Report.query.filter(
            ~Report.user_id.in_(db.session.query(User.id))
        ).all()
        
        if orphan_reports:
            print(f"   ⚠️  {len(orphan_reports)} orphan report bulundu")
            for report in orphan_reports:
                print(f"      - Report #{report.id}: user_id={report.user_id}")
                db.session.delete(report)
            db.session.commit()
            print(f"   ✅ {len(orphan_reports)} orphan report silindi")
        else:
            print("   ✅ Orphan report yok")
        
        # Kullanıcısı olmayan transaction'lar
        orphan_transactions = Transaction.query.filter(
            ~Transaction.user_id.in_(db.session.query(User.id))
        ).all()
        
        if orphan_transactions:
            print(f"   ⚠️  {len(orphan_transactions)} orphan transaction bulundu")
            for trans in orphan_transactions:
                print(f"      - Transaction #{trans.id}: user_id={trans.user_id}")
                db.session.delete(trans)
            db.session.commit()
            print(f"   ✅ {len(orphan_transactions)} orphan transaction silindi")
        else:
            print("   ✅ Orphan transaction yok")

def fix_credit_mismatch():
    """Kredi uyuşmazlıklarını düzelt"""
    print("\n🔧 Kredi uyuşmazlıkları kontrol ediliyor...")
    
    app = create_app()
    with app.app_context():
        users = User.query.all()
        fixed_count = 0
        
        for user in users:
            # Transaction'lardan gerçek kredileri hesapla
            purchases = db.session.query(
                db.func.sum(Transaction.amount)
            ).filter(
                Transaction.user_id == user.id,
                Transaction.transaction_type == 'purchase',
                Transaction.status == 'completed'
            ).scalar() or 0
            
            usage = db.session.query(
                db.func.sum(Transaction.amount)
            ).filter(
                Transaction.user_id == user.id,
                Transaction.transaction_type == 'usage'
            ).scalar() or 0
            
            expected_credits = purchases - usage
            
            if user.credits != expected_credits:
                print(f"   ⚠️  {user.username}: {user.credits} → {expected_credits}")
                user.credits = expected_credits
                fixed_count += 1
        
        if fixed_count > 0:
            db.session.commit()
            print(f"   ✅ {fixed_count} kullanıcının kredisi düzeltildi")
        else:
            print("   ✅ Kredi uyuşmazlığı yok")

def add_missing_indexes():
    """Eksik index'leri ekle"""
    print("\n🔧 Index'ler kontrol ediliyor...")
    
    app = create_app()
    with app.app_context():
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_reports_user_created ON reports(user_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_user_created ON transactions(user_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type)",
            "CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(email_verified)",
        ]
        
        for idx_sql in indexes:
            try:
                db.session.execute(text(idx_sql))
                idx_name = idx_sql.split("INDEX IF NOT EXISTS ")[1].split(" ON ")[0]
                print(f"   ✅ {idx_name}")
            except Exception as e:
                print(f"   ⚠️  Index hatası: {e}")
        
        db.session.commit()

def ensure_settings_exists():
    """Settings kaydının var olduğundan emin ol"""
    print("\n🔧 Settings kontrol ediliyor...")
    
    app = create_app()
    with app.app_context():
        settings = Settings.query.first()
        
        if not settings:
            print("   ⚠️  Settings kaydı yok, oluşturuluyor...")
            settings = Settings(
                site_name='RaporcuAI',
                site_description='Yapay zeka destekli rapor oluşturma platformu',
                theme_color='#4e73df',
                default_report_cost=1,
                welcome_bonus_credits=2,
                enable_registration=True,
                enable_email_verification=False,
                default_ai_model='openai'
            )
            db.session.add(settings)
            db.session.commit()
            print("   ✅ Settings oluşturuldu")
        else:
            # Eksik alanları doldur
            updated = False
            if not settings.theme_color:
                settings.theme_color = '#4e73df'
                updated = True
            if not settings.default_report_cost:
                settings.default_report_cost = 1
                updated = True
            if settings.welcome_bonus_credits is None:
                settings.welcome_bonus_credits = 2
                updated = True
            
            if updated:
                db.session.commit()
                print("   ✅ Settings güncellendi")
            else:
                print("   ✅ Settings tamam")

def ensure_packages_exist():
    """Kredi paketlerinin var olduğundan emin ol"""
    print("\n🔧 Kredi paketleri kontrol ediliyor...")
    
    app = create_app()
    with app.app_context():
        package_count = CreditPackage.query.count()
        
        if package_count == 0:
            print("   ⚠️  Hiç paket yok, varsayılan paketler oluşturuluyor...")
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
                )
            ]
            
            for pkg in packages:
                db.session.add(pkg)
            
            db.session.commit()
            print(f"   ✅ {len(packages)} paket oluşturuldu")
        else:
            print(f"   ✅ {package_count} paket mevcut")

def vacuum_analyze():
    """PostgreSQL VACUUM ANALYZE çalıştır (performans için)"""
    print("\n🔧 Veritabanı optimize ediliyor...")
    
    app = create_app()
    with app.app_context():
        try:
            # SQLite için bu komut çalışmaz, sadece PostgreSQL için
            if 'postgresql' in str(db.engine.url):
                db.session.execute(text("VACUUM ANALYZE"))
                db.session.commit()
                print("   ✅ VACUUM ANALYZE tamamlandı")
            else:
                print("   ℹ️  SQLite için VACUUM gerekli değil")
        except Exception as e:
            print(f"   ⚠️  VACUUM hatası: {e}")

def main():
    """Tüm düzeltmeleri çalıştır"""
    print("=" * 60)
    print("🔧 VERİTABANI TROUBLESHOOTING")
    print("=" * 60)
    
    try:
        fix_orphan_records()
        fix_credit_mismatch()
        add_missing_indexes()
        ensure_settings_exists()
        ensure_packages_exist()
        vacuum_analyze()
        
        print("\n" + "=" * 60)
        print("✅ TÜM DÜZELTMELER TAMAMLANDI")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

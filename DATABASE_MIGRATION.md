# Database Yönetimi ve Taşıma Kılavuzu

## Hızlı Kontrol

```bash
# Veritabanı sağlık kontrolü
python database_check.py
```

## Veritabanı Başlatma (İlk Kurulum)

```bash
# Tüm tabloları oluştur ve initial data ekle
python init_db.py
```

## Migration Yönetimi

### Yeni Migration Oluşturma
```bash
# Modellerdeki değişiklikleri tespit et
flask db migrate -m "Açıklama"

# Migration'ı uygula
flask db upgrade

# Geri al
flask db downgrade
```

### Mevcut Migration'ları Uygula
```bash
# Tüm migration'ları uygula
flask db upgrade

# Belirli bir versiyona git
flask db upgrade 002
```

## Veritabanı Yedeği

### PostgreSQL Dump (Önerilen)
```bash
# Sunucuda full backup
pg_dump -U raporcuweb -d raporcuweb -F c -f backup_$(date +%Y%m%d_%H%M%S).dump

# Docker üzerinden
docker-compose exec postgres pg_dump -U raporcuweb raporcuweb > backup.sql

# Sadece data
pg_dump -U raporcuweb -d raporcuweb --data-only -f data_backup.sql

# Sadece schema
pg_dump -U raporcuweb -d raporcuweb --schema-only -f schema_backup.sql
```

### Geri Yükleme
```bash
# .dump dosyasından
pg_restore -U raporcuweb -d raporcuweb_new backup.dump

# .sql dosyasından
psql -U raporcuweb -d raporcuweb_new < backup.sql
```

## Başka Sunucuya Taşıma

### 1. Yöntem: PostgreSQL Dump/Restore

#### Eski Sunucuda:
```bash
# Backup al
cd /opt/raporcuweb
docker-compose exec postgres pg_dump -U raporcuweb raporcuweb -F c > raporcuweb_backup.dump

# Lokal makineye indir (başka terminalden)
scp root@178.208.187.30:/opt/raporcuweb/raporcuweb_backup.dump ./
```

#### Yeni Sunucuda:
```bash
# Projeyi kur
git clone https://github.com/rraeyz/raporcuweb.git
cd raporcuweb

# Docker başlat
docker-compose up -d postgres

# Backup'ı yükle
cat raporcuweb_backup.dump | docker-compose exec -T postgres pg_restore -U raporcuweb -d raporcuweb

# Web servisi başlat
docker-compose up -d web
```

### 2. Yöntem: SQL Export/Import

#### Eski Sunucuda:
```bash
# SQL export
docker-compose exec postgres pg_dump -U raporcuweb raporcuweb > backup.sql

# Sıkıştır (isteğe bağlı)
gzip backup.sql
```

#### Yeni Sunucuda:
```bash
# Sıkıştırılmışsa aç
gunzip backup.sql.gz

# Import et
cat backup.sql | docker-compose exec -T postgres psql -U raporcuweb -d raporcuweb
```

### 3. Yöntem: Docker Volume Copy

```bash
# Eski sunucuda volume'ü tar'la
docker run --rm -v raporcuweb_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_data.tar.gz -C /data .

# Yeni sunucuya kopyala
scp postgres_data.tar.gz root@yeni-sunucu:/opt/raporcuweb/

# Yeni sunucuda volume'e geri yükle
docker run --rm -v raporcuweb_postgres_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/postgres_data.tar.gz -C /data
```

## Uploads ve Temp Dosyaları

```bash
# Eski sunucuda
cd /opt/raporcuweb
tar czf uploads_backup.tar.gz uploads/ temp/

# Yeni sunucuya kopyala
scp uploads_backup.tar.gz root@yeni-sunucu:/opt/raporcuweb/

# Yeni sunucuda
tar xzf uploads_backup.tar.gz
```

## Taşıma Checklist

- [ ] Veritabanı yedeği alındı (pg_dump)
- [ ] Uploads klasörü yedeklendi
- [ ] Temp klasörü yedeklendi (gerekirse)
- [ ] .env dosyası kopyalandı
- [ ] SSL sertifikaları yedeklendi (/etc/acme.sh/)
- [ ] Yeni sunucuda Docker kurulu
- [ ] Yeni sunucuda PostgreSQL restore edildi
- [ ] Yeni sunucuda dosyalar yüklendi
- [ ] Environment variables ayarlandı
- [ ] DNS A kaydı yeni IP'ye güncellendi
- [ ] SSL yeniden yapılandırıldı
- [ ] Uygulama test edildi
- [ ] Eski sunucu kapatıldı

## Sorun Giderme

### Database bağlantı hatası
```bash
# PostgreSQL loglarını kontrol et
docker-compose logs postgres

# Container'ın çalıştığından emin ol
docker-compose ps
```

### Migration hatası
```bash
# Mevcut migration versiyonunu kontrol et
flask db current

# Migration history
flask db history

# Zorla versiyonu ayarla (DİKKAT!)
flask db stamp 003
```

### Orphan data temizleme
```python
# Python shell'de
from app import create_app, db
from app.models.report import Report
from app.models.user import User

app = create_app()
with app.app_context():
    # Kullanıcısı olmayan raporları sil
    orphan_reports = Report.query.filter(
        ~Report.user_id.in_(db.session.query(User.id))
    ).all()
    
    for report in orphan_reports:
        db.session.delete(report)
    
    db.session.commit()
```

## Performans Optimizasyonu

### Index Ekleme
```sql
-- Sık kullanılan sorgu alanlarına index ekle
CREATE INDEX IF NOT EXISTS idx_reports_user_created ON reports(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_user_created ON transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
```

### Vacuum ve Analyze
```bash
# PostgreSQL bakımı
docker-compose exec postgres psql -U raporcuweb -d raporcuweb -c "VACUUM ANALYZE;"
```

## Monitoring

```bash
# Veritabanı boyutu
docker-compose exec postgres psql -U raporcuweb -d raporcuweb -c "SELECT pg_size_pretty(pg_database_size('raporcuweb'));"

# Tablo boyutları
docker-compose exec postgres psql -U raporcuweb -d raporcuweb -c "SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Aktif bağlantılar
docker-compose exec postgres psql -U raporcuweb -d raporcuweb -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'raporcuweb';"
```

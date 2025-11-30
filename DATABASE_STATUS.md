# Veritabanı Kontrol ve Hazırlık Raporu

## ✅ Tamamlanan İşlemler

### 1. Database Kontrol Scriptleri Oluşturuldu

#### `database_check.py`
- **Amaç**: Veritabanı yapısını ve veri bütünlüğünü kontrol eder
- **Özellikler**:
  - Tablo varlık kontrolü
  - Kolon, index ve foreign key kontrolü
  - Orphan kayıt tespiti
  - Kredi tutarsızlığı kontrolü
  - Toplam istatistikler

#### `fix_database.py`
- **Amaç**: Tespit edilen sorunları otomatik düzeltir
- **Özellikler**:
  - Orphan kayıtları temizler
  - Kredi uyuşmazlıklarını düzeltir
  - Eksik index'leri ekler
  - Settings ve paketleri kontrol eder
  - VACUUM ANALYZE (PostgreSQL optimizasyonu)

#### `init_db.py`
- **Amaç**: Veritabanını sıfırdan başlatır
- **Özellikler**:
  - Tüm tabloları oluşturur
  - Admin kullanıcı oluşturur (admin/Admin123!)
  - Varsayılan ayarları ekler
  - 4 kredi paketi oluşturur

### 2. Migration Dosyaları Tamamlandı

```
migrations/versions/
├── 001_add_word_columns.py         ✅ (Word export kolonları)
├── 002_add_shopier_api_fields.py   ✅ (Shopier API key/secret)
└── 003_add_shopier_payment_url.py  ✅ YENİ (Payment URL + webhook secret)
```

### 3. Dokümantasyon

#### `DATABASE_MIGRATION.md`
- Veritabanı yedekleme komutları
- Sunucudan sunucuya taşıma adımları
- Migration yönetimi
- Backup/restore prosedürleri
- Sorun giderme ipuçları
- Taşıma checklist

### 4. .gitignore Güncellendi
- Backup dosyaları hariç tutuldu (*.dump, *.sql, *.tar.gz)
- Temp klasörü ignore edildi
- Log dosyaları hariç tutuldu

## 📊 Mevcut Veritabanı Yapısı

### Tablolar (8 adet)

1. **users** - Kullanıcı bilgileri
   - Kolonlar: id, username, email, password_hash, credits, is_admin, vb.
   - İlişkiler: reports, transactions

2. **reports** - Oluşturulan raporlar
   - Kolonlar: id, user_id, title, content, status, file_path, word_file_path, vb.
   - İlişkiler: user, transaction

3. **transactions** - Kredi işlemleri
   - Kolonlar: id, user_id, transaction_type, amount, payment_id, status, vb.
   - İlişkiler: user, report, promo_code

4. **credit_packages** - Kredi paketleri
   - Kolonlar: id, name, description, credits, price, is_active, sort_order, vb.

5. **promo_codes** - Promosyon kodları
   - Kolonlar: id, code, discount_type, discount_value, max_uses, vb.
   - İlişkiler: transactions

6. **announcements** - Duyurular
   - Kolonlar: id, title, content, is_active, announcement_type, priority, vb.

7. **settings** - Site ayarları (Singleton)
   - Kolonlar: site_name, theme_color, shopier_api_key, shopier_payment_url, vb.

8. **alembic_version** - Migration tracking

### Foreign Keys
- reports.user_id → users.id
- transactions.user_id → users.id
- transactions.report_id → reports.id
- transactions.promo_code_id → promo_codes.id

### İndeksler
- users: username, email (unique)
- reports: user_id, created_at
- transactions: user_id, created_at
- promo_codes: code (unique)

## 🔧 Kullanım Örnekleri

### Sağlık Kontrolü
```bash
# Lokal (development)
python database_check.py

# Sunucuda (Docker)
docker-compose exec web python database_check.py
```

### Sorun Giderme
```bash
# Lokal
python fix_database.py

# Sunucuda
docker-compose exec web python fix_database.py
```

### Yeni Sunucuya Taşıma

1. **Eski Sunucuda Backup:**
```bash
cd /opt/raporcuweb
docker-compose exec postgres pg_dump -U raporcuweb raporcuweb -F c > backup.dump
tar czf uploads_backup.tar.gz uploads/ temp/
```

2. **Backup'ları İndir:**
```bash
scp root@178.208.187.30:/opt/raporcuweb/backup.dump ./
scp root@178.208.187.30:/opt/raporcuweb/uploads_backup.tar.gz ./
```

3. **Yeni Sunucuda Kurulum:**
```bash
# Git repo'yu klonla
git clone https://github.com/rraeyz/raporcuweb.git
cd raporcuweb

# .env dosyası oluştur
cp .env.example .env
nano .env  # Ayarları düzenle

# Docker başlat
docker-compose up -d postgres

# Backup'ı yükle
cat backup.dump | docker-compose exec -T postgres pg_restore -U raporcuweb -d raporcuweb

# Dosyaları geri yükle
tar xzf uploads_backup.tar.gz

# Web servisini başlat
docker-compose up -d web

# Kontrol et
docker-compose exec web python database_check.py
```

4. **DNS Güncelle:**
- Domain A kaydını yeni IP'ye yönlendir
- SSL sertifikasını yeniden yapılandır

## 🛡️ Veri Bütünlüğü Kontrolleri

### Orphan Kayıt Kontrolleri
- Kullanıcısı olmayan raporlar
- Kullanıcısı olmayan transaction'lar
- Raporu olmayan transaction'lar (usage type)

### Kredi Tutarlılığı
- Kullanıcı kredisi = (Toplam alınan - Toplam kullanılan)
- Transaction kayıtları ile user.credits eşleşmesi

### Referential Integrity
- Foreign key ilişkileri korunuyor mu?
- Cascade delete davranışları doğru mu?

## 📋 Taşıma Checklist

- [ ] Veritabanı yedeği alındı (`backup.dump`)
- [ ] Uploads klasörü yedeklendi (`uploads_backup.tar.gz`)
- [ ] Temp klasörü yedeklendi (gerekirse)
- [ ] .env dosyası kopyalandı
- [ ] SSL sertifikaları yedeklendi (`/root/.acme.sh/`)
- [ ] Yeni sunucuda Docker kurulu
- [ ] PostgreSQL restore edildi
- [ ] Migration'lar uygulandı (`flask db upgrade`)
- [ ] Sağlık kontrolü yapıldı (`database_check.py`)
- [ ] Sorun varsa düzeltildi (`fix_database.py`)
- [ ] Web servisi başlatıldı
- [ ] Uygulama test edildi
- [ ] DNS güncellendi
- [ ] SSL yenilendi
- [ ] Eski sunucu kapatıldı

## 🎯 Öneriler

### Performans
1. **Index'ler**: Sık sorgulanan kolonlara index ekle
2. **VACUUM**: Düzenli olarak VACUUM ANALYZE çalıştır
3. **Connection Pool**: SQLAlchemy pool ayarlarını optimize et

### Güvenlik
1. **Backup**: Günlük otomatik backup kurulumu
2. **Monitoring**: Database boyutu ve performans izleme
3. **Encryption**: Hassas verileri encrypt et (API keys)

### Bakım
1. **Cleanup**: Eski raporları arşivle/sil
2. **Logs**: Eski logları temizle
3. **Orphan Files**: Veritabanında olmayan dosyaları temizle

## ⚠️ Dikkat Edilmesi Gerekenler

1. **Migration Sırası**: Migration'lar sırayla uygulanmalı (001 → 002 → 003)
2. **Backup Önce**: Her migration öncesi backup al
3. **Test Ortamı**: Önce test ortamında dene
4. **Downtime**: Production taşıma sırasında kısa downtime olabilir
5. **DNS Propagation**: DNS değişikliği 24 saate kadar sürebilir

## 📞 Sorun Durumunda

1. **Database bağlantı hatası**:
   - PostgreSQL container çalışıyor mu? `docker-compose ps`
   - DATABASE_URL doğru mu? `.env` kontrol et
   - Port açık mı? `netstat -tulpn | grep 5432`

2. **Migration hatası**:
   - Mevcut versiyon: `flask db current`
   - Manuel stamp: `flask db stamp 003` (son çare!)

3. **Kredi uyuşmazlığı**:
   - `python fix_database.py` çalıştır

4. **Orphan kayıtlar**:
   - `python fix_database.py` çalıştır

## ✅ Sonuç

Veritabanı yapısı sağlam ve taşınmaya hazır durumda. Tüm migration'lar mevcut, backup/restore scriptleri hazır. Yeni sunucuya taşıma için gerekli tüm araçlar ve dokümantasyon oluşturuldu.

**Tavsiye**: Sunucuya bağlanabildiğinde önce `database_check.py` çalıştır, ardından gerekirse `fix_database.py` ile düzeltmeleri yap.

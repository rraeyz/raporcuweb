# Render.com'a Deployment Rehberi

## 🚀 Hızlı Başlangıç

### 1. GitHub'a Push
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/KULLANICI_ADINIZ/raporcuweb.git
git push -u origin main
```

### 2. Render.com'a Kayıt
1. [render.com](https://render.com) adresine git
2. GitHub ile giriş yap
3. Repository'nize erişim izni ver

### 3. Web Service Oluştur
1. Dashboard'da **"New +"** → **"Web Service"**
2. Repository'nizi seç: `raporcuweb`
3. Ayarlar:
   - **Name:** `raporcuweb`
   - **Region:** Frankfurt (Avrupa)
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn run:app`
   - **Plan:** Free

### 4. PostgreSQL Database Oluştur
1. Dashboard'da **"New +"** → **"PostgreSQL"**
2. Ayarlar:
   - **Name:** `raporcuweb-db`
   - **Region:** Frankfurt (aynı region)
   - **Plan:** Free
3. **Create Database** tıkla

### 5. Environment Variables Ekle
Web Service → **Environment** sekmesi:

**Zorunlu:**
```
DATABASE_URL = [PostgreSQL'den Internal Database URL'yi kopyala]
SECRET_KEY = [Rastgele 50 karakter - aşağıdaki komutu çalıştır]
FLASK_ENV = production
```

**SECRET_KEY oluşturmak için:**
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

**Opsiyonel (AI API'ları):**
```
OPENAI_API_KEY = sk-...
ANTHROPIC_API_KEY = sk-ant-...
GOOGLE_API_KEY = AIza...
```

**Opsiyonel (Email - Gmail SMTP):**
```
MAIL_USERNAME = yourmail@gmail.com
MAIL_PASSWORD = [Gmail App Password]
MAIL_DEFAULT_SENDER = noreply@raporcuweb.com
```

### 6. Deploy
1. **"Create Web Service"** tıkla
2. İlk deployment otomatik başlar (3-5 dakika)
3. Logs'u takip et
4. Başarılı olunca: `https://raporcuweb.onrender.com` aktif!

---

## 🔧 Önemli Notlar

### Database Migration
İlk deployment sonrası admin kullanıcı oluşturmak için:
```bash
# Render Dashboard → Shell (Web Service içinde)
python -c "from app import create_app, db; from app.models import User; app = create_app(); app.app_context().push(); admin = User(username='admin', email='admin@example.com', is_admin=True); admin.set_password('Admin123!'); db.session.add(admin); db.session.commit(); print('Admin created!')"
```

### Free Tier Limitler
- ✅ 750 saat/ay (yeterli)
- ⚠️ 15 dakika inaktivitede uyur
- ✅ 512MB RAM
- ✅ PostgreSQL 1GB depolama

### Server Uyanık Tutma (UptimeRobot)
1. [uptimerobot.com](https://uptimerobot.com) → Kayıt ol
2. **Add New Monitor**
3. URL: `https://raporcuweb.onrender.com`
4. Interval: 5 dakika
5. ✅ Server artık hiç uyumaz!

### SSL/HTTPS
- ✅ Otomatik aktif (Let's Encrypt)
- ✅ Sertifika otomatik yenilenir

### Logs
Dashboard → Logs sekmesinden canlı takip edebilirsiniz.

---

## 🐛 Sorun Giderme

### Build başarısız olursa:
```bash
# requirements.txt'de versiyon çakışması varsa
pip freeze > requirements.txt  # Güncel versiyonlar
```

### Database bağlantı hatası:
- Environment'ta `DATABASE_URL` doğru mu kontrol et
- PostgreSQL ve Web Service aynı region'da mı?

### 502 Bad Gateway:
- Start command doğru mu: `gunicorn run:app`
- Port 10000 dinliyor mu (Render otomatik)

---

## 📱 İletişim

Sorun yaşarsan Render Dashboard'dan **Support** ile iletişime geçebilirsin.

**Deployment başarılı! 🎉**

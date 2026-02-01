# 📝 RaporcuWeb - Yapay Zeka Destekli Rapor Oluşturma Platformu

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

</div>

RaporcuWeb, kullanıcıların yapay zeka desteğiyle hızlı ve profesyonel raporlar oluşturmasını sağlayan modern bir web uygulamasıdır. OpenAI GPT-4, Anthropic Claude ve Google Gemini gibi lider AI modellerini destekler.

## 🚀 Özellikler

### 🎨 Kullanıcı Deneyimi
- 🔐 **Güvenli Kimlik Doğrulama:** Kullanıcı kayıt/giriş sistemi
- ✉️ **E-posta Doğrulama:** Hesap güvenliği için
- 🔑 **Şifre Sıfırlama:** Güvenli şifre kurtarma
- 💰 **Kredi Sistemi:** Esnek kullanım bazlı model
- 🤖 **Multi-AI Desteği:** OpenAI, Anthropic ve Google AI entegrasyonu
- 📄 **PDF İndirme:** Profesyonel rapor çıktıları
- 📊 **Rapor Geçmişi:** Tüm raporlarınıza kolay erişim
- 📈 **İşlem Takibi:** Detaylı işlem geçmişi

### 💳 Ödeme ve Market
- 💎 **Kredi Paketleri:** Farklı kullanım senaryoları için
- 🛒 **Shopier Entegrasyonu:** Güvenli ödeme altyapısı
- 🎟️ **Promosyon Kodları:** İndirim ve kampanya desteği
- 🔒 **Güvenli İşlemler:** PCI uyumlu ödeme sistemi

### 👨‍💼 Admin Paneli
- 👥 **Kullanıcı Yönetimi:** Tam kontrol
- 💼 **Kredi Paketi Yönetimi:** Fiyatlandırma kontrolü
- 🎫 **Promosyon Sistemi:** Kampanya oluşturma
- 📢 **Duyuru Sistemi:** Kullanıcı bildirimleri
- ⚙️ **Site Ayarları:** Merkezi konfigürasyon
- 📊 **İstatistikler:** Detaylı raporlama ve analiz

### 🔒 Güvenlik ve Performans
- 🛡️ **CSRF Koruması:** Cross-site request forgery önleme
- ⏱️ **Rate Limiting:** Kötüye kullanım engelleme
- 🔐 **XSS Koruması:** Cross-site scripting güvenliği
- 🔑 **Bcrypt Hashing:** Güvenli şifre hashleme
- 📝 **Session Yönetimi:** Güvenli oturum kontrolü

## 📋 Teknoloji Stack

### Backend
- **Framework:** Flask 3.0+
- **Database:** SQLAlchemy (SQLite/PostgreSQL)
- **Migration:** Flask-Migrate
- **Authentication:** Flask-Login
- **Email:** Flask-Mail
- **Forms:** Flask-WTF

### AI/ML
- **OpenAI:** GPT-4, GPT-4 Turbo
- **Anthropic:** Claude 3 Opus, Claude 3 Sonnet
- **Google:** Gemini Pro, Gemini Flash

### Frontend
- **UI Framework:** Bootstrap 5
- **Icons:** Font Awesome
- **Charts:** Chart.js

### Payment
- **Gateway:** Shopier

## 💻 Gereksinimler

- Python 3.8+
- PostgreSQL veya SQLite (development için)
- SMTP sunucusu (e-posta gönderimi için)
- AI API anahtarları (OpenAI, Anthropic veya Google)
- Shopier hesabı (ödeme entegrasyonu için)

## 🛠️ Kurulum

### 1. Projeyi Klonlayın

```bash
git clone https://github.com/rraeyz/raporcuweb.git
cd raporcuweb
```

### 2. Virtual Environment Oluşturun

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Bağımlılıkları Yükleyin

```powershell
pip install -r requirements.txt
```

### 4. Environment Değişkenlerini Ayarlayın

`.env.example` dosyasını `.env` olarak kopyalayın ve değerleri düzenleyin:

```powershell
copy .env.example .env
```

`.env` dosyasında şunları yapılandırın:
- `SECRET_KEY`: Güvenli bir secret key oluşturun
- `DATABASE_URL`: Veritabanı bağlantı URL'i
- `MAIL_*`: E-posta ayarları
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`: AI API anahtarları
- `SHOPIER_*`: Shopier ödeme bilgileri

### 5. Veritabanını Başlatın

```powershell
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6. Uygulamayı Çalıştırın

```powershell
python run.py
```

Uygulama varsayılan olarak `http://localhost:5000` adresinde çalışacaktır.

## 👤 Varsayılan Admin Hesabı

İlk çalıştırmada otomatik olarak bir admin hesabı oluşturulur:

- **E-posta**: admin@raporcuweb.com
- **Şifre**: Admin123!

⚠️ **ÖNEMLİ**: Production ortamında bu şifreyi mutlaka değiştirin!

## 📁 Proje Yapısı

```
raporcuweb/
├── app/
│   ├── models/          # Veritabanı modelleri
│   ├── routes/          # Flask route'ları (blueprints)
│   ├── services/        # Servis katmanı (AI, Email, Payment vb.)
│   ├── utils/           # Yardımcı fonksiyonlar
│   ├── static/          # CSS, JS, resimler
│   └── templates/       # HTML template'leri
├── migrations/          # Veritabanı migration'ları
├── uploads/            # Kullanıcı dosyaları
├── config.py           # Uygulama konfigürasyonu
├── requirements.txt    # Python bağımlılıkları
├── run.py             # Ana çalıştırma dosyası
└── .env               # Environment değişkenleri
```

## 🎯 Kullanım

### Yeni Rapor Oluşturma

1. Giriş yapın veya yeni hesap oluşturun
2. Dashboard'dan "Yeni Rapor" butonuna tıklayın
3. Rapor başlığını ve içeriğini girin
4. AI modelini seçin
5. "Raporu Oluştur" butonuna tıklayın
6. AI raporunuzu oluşturduğunda görüntüleyin ve PDF olarak indirin

### Kredi Satın Alma

1. "Kredi Al" menüsüne gidin
2. Uygun paketi seçin
3. Shopier ödeme sayfasına yönlendirileceksiniz
4. Ödeme tamamlandıktan sonra krediler otomatik olarak hesabınıza tanımlanır

### Admin Paneli

1. Admin hesabıyla giriş yapın
2. Üst menüden "Admin Paneli"ne tıklayın
3. Şunları yapabilirsiniz:
   - Kullanıcıları yönetin
   - Kredi paketlerini düzenleyin
   - Promosyon kodları oluşturun
   - Duyuru yayınlayın
   - Site ayarlarını yapılandırın

## 🔧 Konfigürasyon

### AI Modelleri

`.env` dosyasında AI API anahtarlarınızı ayarlayın:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
```

### E-posta Ayarları

Gmail kullanıyorsanız:

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

⚠️ Gmail için "Uygulama Şifresi" oluşturmanız gerekebilir.

### Shopier Entegrasyonu

1. [Shopier](https://www.shopier.com/) hesabı oluşturun
2. API anahtarlarınızı alın
3. Admin panelinden ödeme linkini yapılandırın

## 🚀 Production Deployment

### 1. Environment Ayarları

```
FLASK_ENV=production
SECRET_KEY=very-secure-random-key
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### 2. Gunicorn ile Çalıştırma

```bash
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

### 3. Nginx Yapılandırması

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/raporcuweb/app/static;
    }
}
```

## 📊 Veritabanı

### SQLite (Development)

Varsayılan olarak SQLite kullanılır. Herhangi bir kurulum gerektirmez.

### PostgreSQL (Production)

```bash
# PostgreSQL kurulumu (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# Veritabanı oluşturma
sudo -u postgres createdb raporcuweb
```

`.env` dosyasında:
```
DATABASE_URL=postgresql://username:password@localhost/raporcuweb
```

## 🔒 Güvenlik Önerileri

1. ✅ `SECRET_KEY` değerini güçlü ve rastgele yapın
2. ✅ Production'da `DEBUG=False` olduğundan emin olun
3. ✅ HTTPS kullanın
4. ✅ Düzenli olarak bağımlılıkları güncelleyin
5. ✅ Veritabanı yedeklemesi alın
6. ✅ Rate limiting ayarlarını yapın
7. ✅ Güvenlik duvarı kurallarını ayarlayın

## 🐛 Sorun Giderme

### Import Hataları

```powershell
pip install --upgrade -r requirements.txt
```

### Veritabanı Hataları

```powershell
flask db stamp head
flask db migrate
flask db upgrade
```

### E-posta Gönderimi Sorunları

- SMTP ayarlarını kontrol edin
- Gmail kullanıyorsanız "Daha az güvenli uygulamalara erişim" açık olmalı veya "Uygulama Şifresi" kullanın
- Firewall/antivirus SMTP portunu engelliyor olabilir

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📧 İletişim

Sorularınız için issue açabilirsiniz.

## 🙏 Teşekkürler

Bu proje aşağıdaki harika açık kaynak projeler sayesinde mümkün oldu:

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Bootstrap](https://getbootstrap.com/) - UI components
- [Font Awesome](https://fontawesome.com/) - Icons
- [OpenAI](https://openai.com/) - GPT models
- [Anthropic](https://www.anthropic.com/) - Claude models  
- [Google AI](https://ai.google.dev/) - Gemini models

---

<div align="center">

**⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!**

Made with ❤️ by [rraeyz](https://github.com/rraeyz)

</div>

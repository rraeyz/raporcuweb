# RaporcuWeb ile başlamak için:

## Hızlı Başlangıç

1. Virtual environment oluştur ve aktifleştir:
```powershell
python -m venv venv
.\venv\Scripts\activate
```

2. Bağımlılıkları yükle:
```powershell
pip install -r requirements.txt
```

3. .env dosyasını yapılandır:
```powershell
copy .env.example .env
# .env dosyasını düzenle
```

4. Uygulamayı çalıştır:
```powershell
python run.py
```

5. Tarayıcıda aç: http://localhost:5000

## Varsayılan Admin Giriş:
- E-posta: admin@raporcuweb.com
- Şifre: Admin123!

⚠️ Production'da bu şifreyi değiştirin!

## Önemli Notlar:

### E-posta Ayarları
- Gmail kullanıyorsanız "Uygulama Şifresi" oluşturun
- .env dosyasında MAIL_* değişkenlerini ayarlayın

### AI API Anahtarları
- En az bir AI servisinin API anahtarını .env'ye ekleyin
- Önerilen: OpenAI (en stabil sonuçlar için)

### Shopier Ödeme
- Admin panelden Shopier ödeme linkini yapılandırın
- Test modunda çalışmak için demo link kullanabilirsiniz

### Veritabanı
- Development: SQLite (otomatik)
- Production: PostgreSQL önerilir

## Sorun mu yaşıyorsunuz?

1. Virtual environment aktif mi kontrol edin
2. Tüm bağımlılıklar yüklü mü: `pip list`
3. .env dosyası doğru yapılandırılmış mı
4. 5000 portu kullanımda değil mi

Detaylı bilgi için README.md dosyasına bakın.

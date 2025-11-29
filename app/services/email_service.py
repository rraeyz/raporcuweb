from flask_mail import Message
from app import mail
from flask import current_app, render_template_string
import threading

def send_async_email(app, msg):
    """E-postayı arka planda gönder"""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f'E-posta gönderme hatası: {str(e)}')

def send_email(subject, recipients, text_body=None, html_body=None, sender=None):
    """E-posta gönder"""
    if sender is None:
        sender = current_app.config['MAIL_DEFAULT_SENDER']
    
    msg = Message(subject, sender=sender, recipients=recipients)
    
    if text_body:
        msg.body = text_body
    if html_body:
        msg.html = html_body
    
    # Asenkron olarak gönder
    app = current_app._get_current_object()
    thread = threading.Thread(target=send_async_email, args=(app, msg))
    thread.start()
    
    return True

def send_verification_email(user, token):
    """E-posta doğrulama maili gönder"""
    from flask import url_for
    
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    
    html_body = f'''
    <h2>E-posta Adresinizi Doğrulayın</h2>
    <p>Merhaba {user.username},</p>
    <p>RaporcuWeb hesabınızı oluşturduğunuz için teşekkür ederiz. E-posta adresinizi doğrulamak için aşağıdaki bağlantıya tıklayın:</p>
    <p><a href="{verify_url}" style="background-color: #4e73df; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">E-postamı Doğrula</a></p>
    <p>Veya şu bağlantıyı tarayıcınıza kopyalayın: {verify_url}</p>
    <p>Bu bağlantı 24 saat geçerlidir.</p>
    <p>İyi günler dileriz,<br>RaporcuWeb Ekibi</p>
    '''
    
    text_body = f'''
    E-posta Adresinizi Doğrulayın
    
    Merhaba {user.username},
    
    RaporcuWeb hesabınızı oluşturduğunuz için teşekkür ederiz. E-posta adresinizi doğrulamak için aşağıdaki bağlantıyı ziyaret edin:
    
    {verify_url}
    
    Bu bağlantı 24 saat geçerlidir.
    
    İyi günler dileriz,
    RaporcuWeb Ekibi
    '''
    
    return send_email(
        subject='E-posta Adresinizi Doğrulayın - RaporcuWeb',
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )

def send_password_reset_email(user, token):
    """Şifre sıfırlama maili gönder"""
    from flask import url_for
    
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    html_body = f'''
    <h2>Şifre Sıfırlama</h2>
    <p>Merhaba {user.username},</p>
    <p>Şifrenizi sıfırlamak için bir istek aldık. Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:</p>
    <p><a href="{reset_url}" style="background-color: #4e73df; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Şifremi Sıfırla</a></p>
    <p>Veya şu bağlantıyı tarayıcınıza kopyalayın: {reset_url}</p>
    <p>Bu bağlantı 1 saat geçerlidir.</p>
    <p>Eğer bu isteği siz yapmadıysanız, bu e-postayı görmezden gelebilirsiniz.</p>
    <p>İyi günler dileriz,<br>RaporcuWeb Ekibi</p>
    '''
    
    text_body = f'''
    Şifre Sıfırlama
    
    Merhaba {user.username},
    
    Şifrenizi sıfırlamak için bir istek aldık. Şifrenizi sıfırlamak için aşağıdaki bağlantıyı ziyaret edin:
    
    {reset_url}
    
    Bu bağlantı 1 saat geçerlidir.
    
    Eğer bu isteği siz yapmadıysanız, bu e-postayı görmezden gelebilirsiniz.
    
    İyi günler dileriz,
    RaporcuWeb Ekibi
    '''
    
    return send_email(
        subject='Şifre Sıfırlama - RaporcuWeb',
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )

def send_welcome_email(user):
    """Hoş geldin e-postası gönder"""
    html_body = f'''
    <h2>RaporcuWeb'e Hoş Geldiniz!</h2>
    <p>Merhaba {user.username},</p>
    <p>Hesabınız başarıyla oluşturuldu ve e-posta adresiniz doğrulandı.</p>
    <p>Artık yapay zeka destekli rapor oluşturma özelliğimizi kullanmaya başlayabilirsiniz.</p>
    <p>Sorularınız için bizimle iletişime geçmekten çekinmeyin.</p>
    <p>İyi günler dileriz,<br>RaporcuWeb Ekibi</p>
    '''
    
    text_body = f'''
    RaporcuWeb'e Hoş Geldiniz!
    
    Merhaba {user.username},
    
    Hesabınız başarıyla oluşturuldu ve e-posta adresiniz doğrulandı.
    
    Artık yapay zeka destekli rapor oluşturma özelliğimizi kullanmaya başlayabilirsiniz.
    
    İyi günler dileriz,
    RaporcuWeb Ekibi
    '''
    
    return send_email(
        subject='Hoş Geldiniz - RaporcuWeb',
        recipients=[user.email],
        text_body=text_body,
        html_body=html_body
    )

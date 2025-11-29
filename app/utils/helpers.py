import re
from datetime import datetime

def slugify(text):
    """Metni URL-friendly slug'a çevir"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text

def format_datetime(dt, format='%d.%m.%Y %H:%M'):
    """Tarih-saat formatla"""
    if dt is None:
        return ''
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime(format)

def format_currency(amount, currency='TL'):
    """Para formatla"""
    return f'{amount:,.2f} {currency}'

def format_number(num):
    """Sayı formatla (binlik ayraçlı)"""
    return f'{num:,}'

def truncate(text, length=100, suffix='...'):
    """Metni kısalt"""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + suffix

def get_file_extension(filename):
    """Dosya uzantısını al"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''

def allowed_file(filename, allowed_extensions={'txt', 'pdf', 'doc', 'docx'}):
    """Dosya uzantısının izin verilenler arasında olup olmadığını kontrol et"""
    return '.' in filename and get_file_extension(filename) in allowed_extensions

def generate_unique_filename(original_filename):
    """Benzersiz dosya adı oluştur"""
    import uuid
    from datetime import datetime
    
    ext = get_file_extension(original_filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:8]
    
    return f'{timestamp}_{unique_id}.{ext}'

def calculate_file_size_mb(size_bytes):
    """Byte cinsinden boyutu MB'a çevir"""
    return size_bytes / (1024 * 1024)

def sanitize_html(html_content):
    """HTML içeriğini temizle (XSS koruması)"""
    import html
    return html.escape(html_content)

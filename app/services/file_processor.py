"""
Dosya işleme servisi - PDF, DOCX, TXT dosyalarından metin çıkarma
"""
import os
import io
from werkzeug.utils import secure_filename

class FileProcessor:
    """Dosya işleme sınıfı"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt']
    
    def extract_text_from_file(self, file):
        """
        Yüklenen dosyadan metin çıkar
        
        Args:
            file: FileStorage object from Flask
            
        Returns:
            tuple: (text, error)
        """
        try:
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext not in self.supported_formats:
                return None, f"Desteklenmeyen dosya formatı: {file_ext}"
            
            # Dosya tipine göre metin çıkar
            if file_ext == '.txt':
                return self._extract_from_txt(file)
            elif file_ext == '.pdf':
                return self._extract_from_pdf(file)
            elif file_ext == '.docx':
                return self._extract_from_docx(file)
            
        except Exception as e:
            return None, f"Dosya işlenirken hata: {str(e)}"
    
    def _extract_from_txt(self, file):
        """TXT dosyasından metin çıkar"""
        try:
            text = file.read().decode('utf-8')
            return text, None
        except UnicodeDecodeError:
            # Farklı encoding'ler dene
            file.seek(0)
            for encoding in ['latin-1', 'cp1254', 'iso-8859-9']:
                try:
                    text = file.read().decode(encoding)
                    return text, None
                except:
                    file.seek(0)
                    continue
            return None, "Dosya okunamadı (encoding hatası)"
    
    def _extract_from_pdf(self, file):
        """PDF dosyasından metin çıkar"""
        try:
            import PyPDF2
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip(), None
            
        except ImportError:
            return None, "PyPDF2 kütüphanesi yüklü değil"
        except Exception as e:
            return None, f"PDF okuma hatası: {str(e)}"
    
    def _extract_from_docx(self, file):
        """DOCX dosyasından metin çıkar"""
        try:
            import docx
            
            doc = docx.Document(io.BytesIO(file.read()))
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip(), None
            
        except ImportError:
            return None, "python-docx kütüphanesi yüklü değil"
        except Exception as e:
            return None, f"DOCX okuma hatası: {str(e)}"

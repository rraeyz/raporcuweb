import os
import markdown2
from datetime import datetime
from flask import current_app
import re
import traceback
import base64
from io import BytesIO

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError as e:
    WEASYPRINT_AVAILABLE = False
    print(f"WeasyPrint import hatası: {e}")

try:
    from latex2mathml.converter import convert as latex2mathml
    LATEX2MATHML_AVAILABLE = True
except ImportError:
    LATEX2MATHML_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use('Agg')  # Headless mode
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class ReportGenerator:
    """Rapor oluşturma ve dönüştürme servisi"""
    
    def __init__(self):
        self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
    
    def process_latex_in_html(self, html, for_pdf=False):
        """HTML içindeki LaTeX formüllerini işle (markdown işleminden SONRA)"""
        try:
            # Önce display math ($$...$$) - daha uzun pattern önce
            def replace_display(match):
                latex = match.group(1).strip()
                
                if for_pdf and MATPLOTLIB_AVAILABLE:
                    try:
                        # Matplotlib ile LaTeX render
                        fig, ax = plt.subplots(figsize=(6, 1))
                        ax.text(0.5, 0.5, f'${latex}$', fontsize=16, ha='center', va='center', transform=ax.transAxes)
                        ax.axis('off')
                        
                        buf = BytesIO()
                        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', transparent=True, pad_inches=0.1)
                        plt.close(fig)
                        
                        img_data = base64.b64encode(buf.getvalue()).decode()
                        return f'<div style="text-align: center; margin: 15px 0;"><img src="data:image/png;base64,{img_data}" alt="Math: {latex}" style="max-width: 100%;"/></div>'
                    except Exception as e:
                        current_app.logger.warning(f'PDF LaTeX render hatası: {e}')
                        return f'<div style="text-align: center;"><code>$${latex}$$</code></div>'
                
                elif not for_pdf and LATEX2MATHML_AVAILABLE:
                    try:
                        mathml = latex2mathml(latex)
                        return f'<div class="math-display" style="text-align: center; margin: 15px 0;">{mathml}</div>'
                    except Exception as e:
                        current_app.logger.warning(f'Word MathML hatası: {e}')
                        return f'<div style="text-align: center;"><code>$${latex}$$</code></div>'
                
                return match.group(0)
            
            html = re.sub(r'\$\$(.+?)\$\$', replace_display, html, flags=re.DOTALL)
            
            # Sonra inline math ($...$) - daha kısa pattern
            def replace_inline(match):
                latex = match.group(1).strip()
                
                if for_pdf and MATPLOTLIB_AVAILABLE:
                    try:
                        # Matplotlib ile inline LaTeX render
                        fig, ax = plt.subplots(figsize=(3, 0.6))
                        ax.text(0.5, 0.5, f'${latex}$', fontsize=13, ha='center', va='center', transform=ax.transAxes)
                        ax.axis('off')
                        
                        buf = BytesIO()
                        plt.savefig(buf, format='png', dpi=200, bbox_inches='tight', transparent=True, pad_inches=0.05)
                        plt.close(fig)
                        
                        img_data = base64.b64encode(buf.getvalue()).decode()
                        return f'<img src="data:image/png;base64,{img_data}" style="vertical-align: middle; max-height: 1.8em;" alt="Math: {latex}"/>'
                    except Exception as e:
                        current_app.logger.warning(f'PDF LaTeX render hatası: {e}')
                        return f'<code>${latex}$</code>'
                
                elif not for_pdf and LATEX2MATHML_AVAILABLE:
                    try:
                        mathml = latex2mathml(latex)
                        return f'<span class="math">{mathml}</span>'
                    except Exception as e:
                        current_app.logger.warning(f'Word MathML hatası: {e}')
                        return f'<code>${latex}$</code>'
                
                return match.group(0)
            
            # Sadece metin içindeki $...$ işle (kod bloklarında değil)
            html = re.sub(r'(?<!<code>)\$([^\$\n]+?)\$(?!</code>)', replace_inline, html)
            
            return html
        except Exception as e:
            current_app.logger.error(f'LaTeX işleme hatası: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            return html
    
    def convert_superscripts_subscripts(self, html):
        """Üslü ve altlı sayıları HTML sup/sub tag'lerine çevir"""
        try:
            # 10^-5 gibi formatları <sup> tag'ine çevir
            html = re.sub(r'(\d+)\^(-?\d+)', r'\1<sup>\2</sup>', html)
            
            # x^2, y^3 gibi formatları da çevir
            html = re.sub(r'([a-zA-Z])\ ?\^\ ?(\d+)', r'\1<sup>\2</sup>', html)
            
            # ×10^-5 gibi çarpma işaretli formatları da çevir  
            html = re.sub(r'(×|x)\s?10\^(-?\d+)', r'\1 10<sup>\2</sup>', html)
            
            # Alt simge için _kullanımı: H_2O -> H<sub>2</sub>O
            html = re.sub(r'([a-zA-Z])_(\d+)', r'\1<sub>\2</sub>', html)
            
            return html
        except Exception as e:
            current_app.logger.error(f'Superscript dönüşüm hatası: {str(e)}')
            return html
    
    def markdown_to_html(self, markdown_text, for_pdf=False):
        """Markdown'u HTML'e çevir - LaTeX desteği ile"""
        # Önce markdown'u HTML'e çevir
        html = markdown2.markdown(
            markdown_text,
            extras=['tables', 'fenced-code-blocks', 'break-on-newline', 'cuddled-lists', 'code-friendly', 'strike', 'task_list']
        )
        
        # Üslü ve altlı sayıları çevir
        html = self.convert_superscripts_subscripts(html)
        
        # Sonra HTML içindeki LaTeX'i işle
        html = self.process_latex_in_html(html, for_pdf=for_pdf)
        
        return html
    
    def generate_pdf(self, content, title, username):
        """Markdown içeriğinden PDF oluştur - WeasyPrint ile"""
        if not WEASYPRINT_AVAILABLE:
            current_app.logger.error("WeasyPrint kullanılamıyor!")
            return None, None, "PDF oluşturulamadı: WeasyPrint kütüphanesi yüklenemedi. Lütfen sistem yöneticisine bildirin."
        
        try:
            # Dosya adı oluştur
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'rapor_{username}_{timestamp}.pdf'
            filepath = os.path.join(self.upload_folder, filename)
            
            # Markdown'u HTML'e çevir (PDF için LaTeX render)
            html_content = self.markdown_to_html(content, for_pdf=True)
            
            # Profesyonel PDF CSS stili
            css_style = """
                @page {
                    size: A4;
                    margin: 2cm;
                }
                
                body {
                    font-family: 'DejaVu Sans', Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.6;
                    color: #1a1a1a;
                    text-align: justify;
                }
                
                h1 {
                    font-size: 24pt;
                    font-weight: bold;
                    color: #1a1a1a;
                    text-align: center;
                    margin-top: 0;
                    margin-bottom: 30px;
                    page-break-after: avoid;
                }
                
                h2 {
                    font-size: 18pt;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-top: 20px;
                    margin-bottom: 12px;
                    page-break-after: avoid;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 5px;
                }
                
                h3 {
                    font-size: 14pt;
                    font-weight: bold;
                    color: #34495e;
                    margin-top: 16px;
                    margin-bottom: 10px;
                    page-break-after: avoid;
                }
                
                h4, h5, h6 {
                    font-size: 12pt;
                    font-weight: bold;
                    color: #555;
                    margin-top: 12px;
                    margin-bottom: 8px;
                    page-break-after: avoid;
                }
                
                p {
                    margin-top: 0;
                    margin-bottom: 12px;
                    orphans: 3;
                    widows: 3;
                }
                
                /* Tablolar */
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                    page-break-inside: avoid;
                }
                
                th {
                    background-color: #3498db;
                    color: white;
                    font-weight: bold;
                    padding: 10px;
                    text-align: left;
                    border: 1px solid #2980b9;
                }
                
                td {
                    padding: 8px;
                    border: 1px solid #ddd;
                }
                
                tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                
                /* Listeler */
                ul, ol {
                    margin: 10px 0;
                    padding-left: 25px;
                }
                
                li {
                    margin-bottom: 6px;
                }
                
                /* Kod blokları */
                pre {
                    background-color: #f4f4f4;
                    border: 1px solid #ddd;
                    border-left: 4px solid #3498db;
                    padding: 12px;
                    margin: 15px 0;
                    overflow-x: auto;
                    page-break-inside: avoid;
                    font-family: 'Courier New', monospace;
                    font-size: 10pt;
                    line-height: 1.4;
                }
                
                code {
                    background-color: #f4f4f4;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                    font-size: 10pt;
                }
                
                /* Blockquote */
                blockquote {
                    border-left: 4px solid #3498db;
                    padding-left: 15px;
                    margin: 15px 0;
                    color: #555;
                    font-style: italic;
                }
                
                /* LaTeX denklemler */
                .math {
                    font-family: 'STIX Two Math', 'Latin Modern Math', serif;
                    font-size: 12pt;
                    text-align: center;
                    margin: 15px 0;
                }
                
                /* Bağlantılar */
                a {
                    color: #3498db;
                    text-decoration: none;
                }
                
                a:hover {
                    text-decoration: underline;
                }
                
                /* Tarih bilgisi */
                .report-meta {
                    color: #777;
                    font-size: 9pt;
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 15px;
                }
                
                /* Sayfa sonları */
                .page-break {
                    page-break-after: always;
                }
            """
            
            # HTML template - sadece içerik (başlık ve tarih HTML'den kaldırıldı)
            html_template = f"""
            <!DOCTYPE html>
            <html lang="tr">
            <head>
                <meta charset="UTF-8">
                <title>{title}</title>
                <style>{css_style}</style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # PDF oluştur - CSS objesi ile
            css_obj = CSS(string=css_style)
            html_obj = HTML(string=html_template)
            html_obj.write_pdf(target=filepath, stylesheets=[css_obj])
            
            # Dosya boyutunu al
            file_size = os.path.getsize(filepath)
            
            return filepath, file_size, None
            
        except Exception as e:
            current_app.logger.error(f'PDF oluşturma hatası: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            return None, None, f'PDF oluşturma hatası: {str(e)}'
    
    def generate_word(self, content, title, username):
        """Markdown içeriğinden Word belgesi oluştur - gelişmiş HTML parsing ile"""
        try:
            # html2docx ile dene, başarısız olursa fallback kullan
            try:
                from htmldocx import HtmlToDocx
                from docx import Document
                
                # Dosya adı oluştur
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'rapor_{username}_{timestamp}.docx'
                filepath = os.path.join(self.upload_folder, filename)
                
                # Markdown'u HTML'e çevir (Word için MathML)
                html_content = self.markdown_to_html(content, for_pdf=False)
                
                # Word belgesi oluştur
                doc = Document()
                
                # HTML'i Word'e dönüştür
                from docx.enum.text import WD_ALIGN_PARAGRAPH
                new_parser = HtmlToDocx()
                new_parser.add_html_to_document(html_content, doc)
                
                # İlk başlığı ortala (H1 veya Heading 1)
                for para in doc.paragraphs[:3]:  # İlk 3 paragraf kontrol et
                    if para.style.name in ['Heading 1', 'Title', 'Heading1']:
                        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        break
                
                # Belgeyi kaydet
                doc.save(filepath)
                
                # Dosya boyutunu al
                file_size = os.path.getsize(filepath)
                
                # Dosyanın gerçekten içerik içerdiğini kontrol et
                if file_size < 5000:  # Çok küçükse sorun var
                    current_app.logger.warning(f'htmldocx küçük dosya oluşturdu ({file_size} bytes), fallback kullanılacak')
                    raise Exception("htmldocx küçük dosya oluşturdu")
                
                return filepath, file_size, None
                
            except (ImportError, Exception) as e:
                current_app.logger.warning(f'htmldocx başarısız ({str(e)}), fallback yöntem kullanılıyor')
                # Fallback: geliştirilmiş markdown parsing
                from docx import Document
                from docx.shared import Pt, RGBColor, Inches
                from docx.enum.text import WD_ALIGN_PARAGRAPH
                
                # Dosya adı oluştur
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'rapor_{username}_{timestamp}.docx'
                filepath = os.path.join(self.upload_folder, filename)
                
                # Word belgesi oluştur
                doc = Document()
                
                # Markdown içeriğini satır satır işle
                first_h1 = True  # İlk H1 başlığını takip et
                lines = content.split('\n')
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    if not line:
                        i += 1
                        continue
                    
                    # Başlıklar
                    if line.startswith('# '):
                        heading = doc.add_heading(line[2:], level=1)
                        if first_h1:
                            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            first_h1 = False
                    elif line.startswith('## '):
                        doc.add_heading(line[3:], level=2)
                    elif line.startswith('### '):
                        doc.add_heading(line[4:], level=3)
                    elif line.startswith('#### '):
                        doc.add_heading(line[5:], level=4)
                    # Liste öğeleri
                    elif line.startswith('- ') or line.startswith('* '):
                        doc.add_paragraph(line[2:], style='List Bullet')
                    elif line.startswith(tuple(f'{j}. ' for j in range(1, 100))):
                        doc.add_paragraph(line.split('. ', 1)[1], style='List Number')
                    # Normal paragraf
                    else:
                        # Kalın metin (**text**) işle
                        paragraph = doc.add_paragraph()
                        parts = line.split('**')
                        for idx, part in enumerate(parts):
                            run = paragraph.add_run(part)
                            if idx % 2 == 1:  # Kalın yapılacak kısımlar
                                run.bold = True
                    
                    i += 1
                
                # Belgeyi kaydet
                doc.save(filepath)
                
                # Dosya boyutunu al
                file_size = os.path.getsize(filepath)
                
                return filepath, file_size, None
            
        except Exception as e:
            current_app.logger.error(f'Word oluşturma hatası: {str(e)}')
            current_app.logger.error(traceback.format_exc())
            return None, None, f'Word oluşturma hatası: {str(e)}'
    
    def get_file_path(self, filename):
        """Dosya yolunu döndür"""
        return os.path.join(self.upload_folder, filename)
    
    def delete_file(self, filepath):
        """Dosyayı sil"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            current_app.logger.error(f'Dosya silme hatası: {str(e)}')
            return False

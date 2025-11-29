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
                        fig = plt.figure(figsize=(4, 1))
                        fig.text(0.5, 0.5, f'${latex}$', fontsize=14, ha='center', va='center')
                        
                        buf = BytesIO()
                        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', transparent=True, pad_inches=0.1)
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
                        fig = plt.figure(figsize=(2, 0.5))
                        fig.text(0.5, 0.5, f'${latex}$', fontsize=12, ha='center', va='center')
                        
                        buf = BytesIO()
                        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', transparent=True, pad_inches=0.05)
                        plt.close(fig)
                        
                        img_data = base64.b64encode(buf.getvalue()).decode()
                        return f'<img src="data:image/png;base64,{img_data}" style="vertical-align: middle; max-height: 1.5em;" alt="Math: {latex}"/>'
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
    
    def markdown_to_html(self, markdown_text, for_pdf=False):
        """Markdown'u HTML'e çevir - LaTeX desteği ile"""
        # Önce markdown'u HTML'e çevir
        html = markdown2.markdown(
            markdown_text,
            extras=['tables', 'fenced-code-blocks', 'break-on-newline', 'cuddled-lists', 'code-friendly', 'strike', 'task_list']
        )
        
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
            
            # HTML template
            date_str = datetime.now().strftime('%d.%m.%Y %H:%M')
            html_template = f"""
            <!DOCTYPE html>
            <html lang="tr">
            <head>
                <meta charset="UTF-8">
                <title>{title}</title>
                <style>{css_style}</style>
            </head>
            <body>
                <h1>{title}</h1>
                <div class="report-meta">
                    Oluşturulma Tarihi: {date_str}
                </div>
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
                
                # Başlık ekle
                from docx.shared import Pt, RGBColor
                from docx.enum.text import WD_ALIGN_PARAGRAPH
                
                title_paragraph = doc.add_heading(title, 0)
                title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                # Tarih bilgisi ekle
                date_str = datetime.now().strftime('%d.%m.%Y %H:%M')
                date_paragraph = doc.add_paragraph(f'Oluşturulma Tarihi: {date_str}')
                date_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                date_paragraph.runs[0].font.size = Pt(9)
                date_paragraph.runs[0].font.color.rgb = RGBColor(128, 128, 128)
                
                # Ayırıcı çizgi
                doc.add_paragraph('_' * 50)
                
                # HTML'i Word'e dönüştür
                new_parser = HtmlToDocx()
                new_parser.add_html_to_document(html_content, doc)
                
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
                
                # Başlık ekle
                title_paragraph = doc.add_heading(title, 0)
                title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                # Tarih bilgisi ekle
                date_str = datetime.now().strftime('%d.%m.%Y %H:%M')
                date_paragraph = doc.add_paragraph(f'Oluşturulma Tarihi: {date_str}')
                date_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                date_paragraph.runs[0].font.size = Pt(9)
                date_paragraph.runs[0].font.color.rgb = RGBColor(128, 128, 128)
                
                # Ayırıcı çizgi
                doc.add_paragraph('_' * 50)
                
                # Markdown içeriğini satır satır işle
                lines = content.split('\n')
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    if not line:
                        i += 1
                        continue
                    
                    # Başlıklar
                    if line.startswith('# '):
                        doc.add_heading(line[2:], level=1)
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

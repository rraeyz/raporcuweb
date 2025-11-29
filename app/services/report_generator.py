import os
import markdown
from datetime import datetime
from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re

class ReportGenerator:
    """Rapor oluşturma ve dönüştürme servisi"""
    
    def __init__(self):
        self.upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
    
    def markdown_to_html(self, markdown_text):
        """Markdown'u HTML'e çevir"""
        html = markdown.markdown(
            markdown_text,
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        return html
    
    def generate_pdf(self, content, title, username):
        """Markdown içeriğinden PDF oluştur"""
        try:
            # Dosya adı oluştur
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'report_{username}_{timestamp}.pdf'
            filepath = os.path.join(self.upload_folder, filename)
            
            # PDF oluştur
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Stil tanımlamaları
            styles = getSampleStyleSheet()
            
            # Başlık stili
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            # Normal metin stili
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                leading=16,
                alignment=TA_JUSTIFY,
                fontName='Helvetica'
            )
            
            # İçerik listesi
            story = []
            
            # Başlık ekle
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.5*cm))
            
            # Tarih ekle
            date_text = f"Oluşturulma Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            date_style = ParagraphStyle('Date', parent=styles['Normal'], fontSize=9, textColor=colors.grey)
            story.append(Paragraph(date_text, date_style))
            story.append(Spacer(1, 1*cm))
            
            # Markdown içeriğini işle
            lines = content.split('\n')
            for line in lines:
                if line.strip():
                    # Başlık kontrolü
                    if line.startswith('# '):
                        text = line[2:].strip()
                        story.append(Paragraph(text, styles['Heading1']))
                        story.append(Spacer(1, 0.3*cm))
                    elif line.startswith('## '):
                        text = line[3:].strip()
                        story.append(Paragraph(text, styles['Heading2']))
                        story.append(Spacer(1, 0.2*cm))
                    elif line.startswith('### '):
                        text = line[4:].strip()
                        story.append(Paragraph(text, styles['Heading3']))
                        story.append(Spacer(1, 0.2*cm))
                    elif line.startswith('- ') or line.startswith('* '):
                        text = '• ' + line[2:].strip()
                        story.append(Paragraph(text, normal_style))
                    elif line.startswith('1. ') or line.startswith('2. ') or line.startswith('3. '):
                        story.append(Paragraph(line, normal_style))
                    else:
                        # Normal paragraf
                        text = line.strip()
                        if text:
                            story.append(Paragraph(text, normal_style))
                            story.append(Spacer(1, 0.2*cm))
            
            # PDF'i oluştur
            doc.build(story)
            
            # Dosya boyutunu al
            file_size = os.path.getsize(filepath)
            
            return filepath, file_size, None
            
        except Exception as e:
            return None, None, f'PDF oluşturma hatası: {str(e)}'
    
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

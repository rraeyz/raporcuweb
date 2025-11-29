from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.report import Report
from app.models.transaction import Transaction
from app.models.settings import Settings
from app.services.ai_service import AIService
from app.services.report_generator import ReportGenerator
from app.services.file_processor import FileProcessor
from app.services.audio_processor import AudioProcessor
from app.utils.decorators import email_verified_required, credits_required
from datetime import datetime
import os

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def list_reports():
    """Raporları listele"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    reports = Report.query.filter_by(user_id=current_user.id)\
        .order_by(Report.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('reports/list.html', reports=reports)

@reports_bp.route('/create', methods=['GET', 'POST'])
@login_required
@credits_required(min_credits=1)
def create_report():
    """Yeni rapor oluştur"""
    settings = Settings.get_settings()
    credit_cost = settings.default_report_cost
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        prompt = request.form.get('prompt', '').strip()
        reference_text = request.form.get('reference_text', '').strip()
        ai_model = request.form.get('ai_model', settings.default_ai_model)
        
        # Validasyon
        if not title or not prompt:
            flash('Başlık ve içerik girmeniz gerekiyor.', 'danger')
            return render_template('reports/create.html', credit_cost=credit_cost)
        
        if len(title) < 3 or len(title) > 200:
            flash('Başlık 3-200 karakter arasında olmalı.', 'danger')
            return render_template('reports/create.html', credit_cost=credit_cost)
        
        if len(prompt) < 10:
            flash('İçerik en az 10 karakter olmalı.', 'danger')
            return render_template('reports/create.html', credit_cost=credit_cost)
        
        # Kredi kontrolü
        if current_user.credits < credit_cost:
            flash(f'Yetersiz kredi. Bu işlem için {credit_cost} krediniz olmalı.', 'danger')
            return redirect(url_for('market.packages'))
        
        # Dosya yükleme işlemi
        file_text = ""
        if 'file_upload' in request.files:
            file = request.files['file_upload']
            if file and file.filename:
                file_processor = FileProcessor()
                extracted_text, error = file_processor.extract_text_from_file(file)
                if extracted_text:
                    file_text = extracted_text
                    flash(f'Dosyadan metin çıkarıldı: {file.filename}', 'success')
                elif error:
                    flash(f'Dosya işleme hatası: {error}', 'warning')
        
        # Ses dosyası yükleme işlemi
        audio_text = ""
        if 'audio_upload' in request.files:
            audio_file = request.files['audio_upload']
            if audio_file and audio_file.filename:
                audio_processor = AudioProcessor()
                transcribed_text, error = audio_processor.process_audio_file(audio_file)
                if transcribed_text:
                    audio_text = transcribed_text
                    flash(f'Ses dosyası metne çevrildi: {audio_file.filename}', 'success')
                elif error:
                    flash(f'Ses işleme hatası: {error}', 'warning')
        
        # Referans metin varsa prompt'a ekle
        full_prompt = prompt
        additional_context = []
        
        if reference_text:
            additional_context.append(f"**Kullanıcı Referans Metni:**\n{reference_text}")
        
        if file_text:
            additional_context.append(f"**Yüklenen Dosya İçeriği:**\n{file_text}")
        
        if audio_text:
            additional_context.append(f"**Ses Kaydı Transkripti:**\n{audio_text}")
        
        if additional_context:
            separator = '\n\n'
            full_prompt = f"{prompt}\n\n{separator.join(additional_context)}"
        
        # AI ile rapor oluştur
        ai_service = AIService(model=ai_model)
        content, error = ai_service.generate_report(full_prompt, title)
        
        if error:
            flash(f'Rapor oluşturulurken hata oluştu: {error}', 'danger')
            return render_template('reports/create.html', credit_cost=credit_cost)
        
        # PDF oluştur
        report_generator = ReportGenerator()
        file_path, file_size, error = report_generator.generate_pdf(content, title, current_user.username)
        
        if error:
            flash(f'PDF oluşturulurken hata oluştu: {error}', 'danger')
            # PDF olmadan da raporu kaydet
            file_path = None
            file_size = None
        
        # Rapor kaydı oluştur
        report = Report(
            user_id=current_user.id,
            title=title,
            content=content,
            prompt=prompt,
            format_type='markdown',
            status='completed',
            credits_used=credit_cost,
            file_path=file_path,
            file_size=file_size,
            ai_model=ai_model
        )
        db.session.add(report)
        
        # Kredi düş
        current_user.deduct_credits(credit_cost)
        
        # Transaction oluştur
        transaction = Transaction(
            user_id=current_user.id,
            transaction_type='usage',
            amount=credit_cost,
            description=f'Rapor oluşturuldu: {title}',
            report_id=report.id,
            status='completed'
        )
        db.session.add(transaction)
        
        db.session.commit()
        
        flash('Rapor başarıyla oluşturuldu!', 'success')
        return redirect(url_for('reports.view_report', report_id=report.id))
    
    return render_template('reports/create.html', credit_cost=credit_cost)

@reports_bp.route('/view/<int:report_id>')
@login_required
def view_report(report_id):
    """Rapor görüntüle"""
    report = Report.query.get_or_404(report_id)
    
    # Yetki kontrolü
    if report.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    return render_template('reports/view.html', report=report)

@reports_bp.route('/download/<int:report_id>')
@login_required
def download_report(report_id):
    """Raporu indir"""
    report = Report.query.get_or_404(report_id)
    
    # Yetki kontrolü
    if report.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    if not report.file_path or not os.path.exists(report.file_path):
        flash('Rapor dosyası bulunamadı.', 'danger')
        return redirect(url_for('reports.view_report', report_id=report.id))
    
    return send_file(
        report.file_path,
        as_attachment=True,
        download_name=f'{report.title}.pdf'
    )

@reports_bp.route('/delete/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    """Raporu sil"""
    report = Report.query.get_or_404(report_id)
    
    # Yetki kontrolü
    if report.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Dosyayı sil
    if report.file_path:
        report_generator = ReportGenerator()
        report_generator.delete_file(report.file_path)
    
    db.session.delete(report)
    db.session.commit()
    
    flash('Rapor başarıyla silindi.', 'success')
    return redirect(url_for('reports.list_reports'))

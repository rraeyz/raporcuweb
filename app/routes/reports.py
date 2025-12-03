from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
import threading
from app.models.report import Report
from app.models.transaction import Transaction
from app.models.settings import Settings
from app.services.ai_service import AIService
from app.services.report_generator import ReportGenerator
from app.services.file_processor import FileProcessor
from app.services.audio_processor import AudioProcessor
import base64
import io
from app.utils.decorators import email_verified_required, credits_required
from datetime import datetime
import os

reports_bp = Blueprint('reports', __name__)

def generate_report_async(app, report_id, full_prompt, title, ai_model, username):
    """Arka planda rapor oluştur"""
    with app.app_context():
        try:
            report = Report.query.get(report_id)
            if not report:
                return
            
            # AI ile rapor oluştur
            ai_service = AIService(model=ai_model)
            content, error = ai_service.generate_report(full_prompt, title)
            
            if error:
                report.status = 'failed'
                report.content = f'Hata: {error}'
                try:
                    db.session.commit()
                except Exception as commit_error:
                    db.session.rollback()
                    current_app.logger.error(f'Report commit error: {commit_error}')
                return
            
            # PDF ve Word oluştur
            # PDF ve Word dosyalarını oluştur
            generator = ReportGenerator()
            
            # PDF oluştur
            pdf_path, pdf_size, pdf_error = generator.generate_pdf(
                content=content,
                title=title,
                username=username
            )
            
            # Word oluştur
            word_path, word_size, word_error = generator.generate_word(
                content=content,
                title=title,
                username=username
            )
            
            # Raporu güncelle
            report.content = content
            report.file_path = pdf_path if not pdf_error else None
            report.word_file_path = word_path if not word_error else None
            report.status = 'completed'
            
            try:
                db.session.commit()
            except Exception as commit_error:
                db.session.rollback()
                current_app.logger.error(f'Report completion commit error: {commit_error}')
                report.status = 'failed'
                report.content = f'Database error: {str(commit_error)}'
                db.session.commit()
            
        except Exception as e:
            try:
                report = Report.query.get(report_id)
                if report:
                    report.status = 'failed'
                    report.content = f'Beklenmeyen hata: {str(e)}'
                    db.session.commit()
            except:
                pass

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
    from app.models.settings import Settings
    settings = Settings.get_settings()
    credit_cost = settings.default_report_cost
    
    # Kullanılabilir AI modellerini kontrol et
    available_models = []
    if settings.openai_api_key:
        available_models.append({
            'id': 'openai',
            'name': 'OpenAI GPT-4',
            'description': 'En gelişmiş yapay zeka modeli'
        })
    if settings.anthropic_api_key:
        available_models.append({
            'id': 'anthropic',
            'name': 'Anthropic Claude',
            'description': 'Güvenli ve tutarlı yapay zeka'
        })
    if settings.google_api_key:
        available_models.append({
            'id': 'google',
            'name': 'Google Gemini',
            'description': 'Google\'ın güçlü dil modeli'
        })
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        prompt = request.form.get('prompt', '').strip()
        reference_text = request.form.get('reference_text', '').strip()
        ai_model = request.form.get('ai_model', settings.default_ai_model)
        
        # Validasyon
        if not title or not prompt:
            flash('Başlık ve içerik girmeniz gerekiyor.', 'danger')
            return render_template('reports/create.html', 
                                 credit_cost=credit_cost,
                                 settings=settings,
                                 available_models=available_models)
        
        if len(title) < 3 or len(title) > 200:
            flash('Başlık 3-200 karakter arasında olmalı.', 'danger')
            return render_template('reports/create.html', 
                                 credit_cost=credit_cost,
                                 settings=settings,
                                 available_models=available_models)
        
        if len(prompt) < 10:
            flash('İçerik en az 10 karakter olmalı.', 'danger')
            return render_template('reports/create.html', 
                                 credit_cost=credit_cost,
                                 settings=settings,
                                 available_models=available_models)
        
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
        
        # Referans metin ve dosya içeriğini birleştir
        full_prompt = prompt
        additional_context = []
        
        if reference_text:
            additional_context.append(f"**REFERANS METİN (Bu metnin yazım tarzını, ton ve üslubunu kullan):**\n{reference_text}")
        
        if file_text:
            additional_context.append(f"**YÜKLENEN DOSYA İÇERİĞİ (Bu bilgileri kullan ve yazım tarzını taklit et):**\n{file_text}")
        
        if audio_text:
            additional_context.append(f"**Ses Kaydı Transkripti:**\n{audio_text}")
        
        if additional_context:
            separator = '\n\n'
            full_prompt = f"{prompt}\n\n{separator.join(additional_context)}"
        
        # API anahtarlarını config'e aktar
        current_app.config['OPENAI_API_KEY'] = settings.openai_api_key
        current_app.config['ANTHROPIC_API_KEY'] = settings.anthropic_api_key
        current_app.config['GOOGLE_API_KEY'] = settings.google_api_key
        
        # Önce "processing" durumunda boş rapor oluştur
        report = Report(
            user_id=current_user.id,
            title=title,
            content='Rapor oluşturuluyor...',
            prompt=prompt,
            format_type='markdown',
            status='processing',
            credits_used=credit_cost,
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
            description=f'Rapor oluşturuluyor: {title}',
            status='completed'
        )
        db.session.add(transaction)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Veritabanı hatası: {str(e)}', 'danger')
            return redirect(url_for('reports.list_reports'))
        
        # Arka planda rapor oluştur
        thread = threading.Thread(
            target=generate_report_async,
            args=(current_app._get_current_object(), report.id, full_prompt, title, ai_model, current_user.username)
        )
        thread.daemon = True
        thread.start()
        
        flash('Raporunuz oluşturuluyor! İşlem tamamlandığında burada görünecek.', 'info')
        return redirect(url_for('reports.list_reports'))
    
    return render_template('reports/create.html', 
                         credit_cost=credit_cost,
                         settings=settings,
                         available_models=available_models)

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
    """PDF olarak raporu indir - varsa kaydedilmiş dosya, yoksa yeniden oluştur"""
    report = Report.query.get_or_404(report_id)
    
    # Yetki kontrolü
    if report.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    try:
        # Önce kaydedilmiş dosya var mı kontrol et
        if report.file_path and os.path.exists(report.file_path):
            filepath = report.file_path
        else:
            # Dosya yoksa yeniden oluştur
            from app.services.report_generator import ReportGenerator
            generator = ReportGenerator()
            filepath, file_size, error = generator.generate_pdf(
                content=report.content,
                title=report.title,
                username=current_user.username
            )
            
            if error:
                flash(f'PDF oluşturma hatası: {error}', 'danger')
                return redirect(url_for('reports.view_report', report_id=report.id))
            
            # Yeni oluşturulan dosyayı kaydet
            report.file_path = filepath
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'PDF path save error: {e}')
                # Dosya oluşturuldu ama path kaydedilemedi, yine de indir
        
        # Dosyayı gönder
        return send_file(
            filepath,
            as_attachment=True,
            download_name=f'{report.title}.pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f'PDF indirme hatası: {str(e)}')
        flash('PDF oluşturulurken bir hata oluştu.', 'danger')
        return redirect(url_for('reports.view_report', report_id=report.id))

@reports_bp.route('/download-word/<int:report_id>')
@login_required
def download_word(report_id):
    """Word olarak raporu indir - varsa kaydedilmiş dosya, yoksa yeniden oluştur"""
    report = Report.query.get_or_404(report_id)
    
    # Yetki kontrolü
    if report.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    try:
        # Önce kaydedilmiş dosya var mı kontrol et
        if report.word_file_path and os.path.exists(report.word_file_path):
            filepath = report.word_file_path
        else:
            # Dosya yoksa yeniden oluştur
            from app.services.report_generator import ReportGenerator
            generator = ReportGenerator()
            filepath, file_size, error = generator.generate_word(
                content=report.content,
                title=report.title,
                username=current_user.username
            )
            
            if error:
                flash(f'Word oluşturma hatası: {error}', 'danger')
                return redirect(url_for('reports.view_report', report_id=report.id))
            
            # Yeni oluşturulan dosyayı kaydet
            report.word_file_path = filepath
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Word path save error: {e}')
                # Dosya oluşturuldu ama path kaydedilemedi, yine de indir
        
        # Dosyayı gönder
        return send_file(
            filepath,
            as_attachment=True,
            download_name=f'{report.title}.docx'
        )
        
    except Exception as e:
        current_app.logger.error(f'Word indirme hatası: {str(e)}')
        flash('Word belgesi oluşturulurken bir hata oluştu.', 'danger')
        return redirect(url_for('reports.view_report', report_id=report.id))

@reports_bp.route('/process-audio', methods=['POST'])
@login_required
def process_audio():
    """Ses kaydını metne çevir"""
    try:
        data = request.get_json()
        audio_data = data.get('audio_data')
        
        if not audio_data:
            return jsonify({'success': False, 'message': 'Ses verisi bulunamadı'}), 400
        
        # Base64 ses verisini decode et
        if 'base64,' in audio_data:
            audio_data = audio_data.split('base64,')[1]
        
        audio_bytes = base64.b64decode(audio_data)
        
        # Geçici dosya oluştur
        from werkzeug.datastructures import FileStorage
        audio_file = FileStorage(
            stream=io.BytesIO(audio_bytes),
            filename='recording.webm',
            content_type='audio/webm'
        )
        
        # Ses işleyici ile metne çevir
        audio_processor = AudioProcessor()
        transcription, error = audio_processor.process_audio_file(audio_file)
        
        if transcription:
            return jsonify({
                'success': True,
                'text': transcription
            })
        else:
            error_msg = error or 'Ses metne dönüştürülemedi. Lütfen daha net konuşmayı deneyin.'
            return jsonify({
                'success': False,
                'message': error_msg
            }), 400
            
    except Exception as e:
        print(f"Audio process error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Ses işlenirken hata oluştu: {str(e)}'
        }), 500

@reports_bp.route('/process-audio-file', methods=['POST'])
@login_required
def process_audio_file():
    """Yüklenmiş ses dosyasını metne çevir"""
    try:
        if 'audio_upload' not in request.files:
            return jsonify({'success': False, 'message': 'Ses dosyası bulunamadı'}), 400
        
        audio_file = request.files['audio_upload']
        if not audio_file or not audio_file.filename:
            return jsonify({'success': False, 'message': 'Geçerli bir ses dosyası seçin'}), 400
        
        audio_processor = AudioProcessor()
        transcription, error = audio_processor.process_audio_file(audio_file)
        
        if transcription:
            return jsonify({'success': True, 'text': transcription})
        else:
            return jsonify({'success': False, 'message': error or 'Ses işlenemedi'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@reports_bp.route('/status/<int:report_id>')
@login_required
def report_status(report_id):
    """Rapor durumunu JSON olarak döndür"""
    report = Report.query.get_or_404(report_id)
    
    # Yetki kontrolü
    if report.user_id != current_user.id:
        return jsonify({'error': 'Yetkisiz erişim'}), 403
    
    return jsonify({
        'id': report.id,
        'title': report.title,
        'status': report.status,
        'created_at': report.created_at.isoformat() if report.created_at else None,
        'has_pdf': report.file_path is not None
    })

@reports_bp.route('/delete/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    """Raporu sil"""
    report = Report.query.get_or_404(report_id)
    
    # Yetki kontrolü
    if report.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    
    # Dosyaları sil (PDF ve Word)
    report_generator = ReportGenerator()
    if report.file_path:
        report_generator.delete_file(report.file_path)
    if report.word_file_path:
        report_generator.delete_file(report.word_file_path)
    
    db.session.delete(report)
    try:
        db.session.commit()
        flash('Rapor başarıyla silindi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Rapor silinirken hata oluştu: {str(e)}', 'danger')
    return redirect(url_for('reports.list_reports'))

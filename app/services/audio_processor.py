"""
Ses dosyası işleme servisi - Google Speech API
"""
import os
import tempfile
import wave
import logging
from flask import current_app
import speech_recognition as sr

# Whisper hosting'de sorunlu - sadece Google Speech API kullanıyoruz
WHISPER_AVAILABLE = False
logger = logging.getLogger(__name__)

class AudioProcessor:
    """Ses dosyası işleme sınıfı"""
    
    def __init__(self):
        self.supported_formats = ['.wav', '.mp3', '.m4a', '.ogg', '.webm']
        self.recognizer = sr.Recognizer()
        self.whisper_model = None
        
        # Speech Recognition optimizasyonları
        self.recognizer.operation_timeout = 60
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 3000
        self.recognizer.pause_threshold = 1
    
    def process_audio_file(self, file):
        """
        Yüklenen ses dosyasını işle ve metne çevir
        
        Args:
            file: FileStorage object from Flask
            
        Returns:
            tuple: (text, error)
        """
        temp_path = None
        optimized_path = None
        
        try:
            # Geçici dizin
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            temp_dir = os.path.join(upload_folder, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Dosyayı geçici olarak kaydet
            import time
            timestamp = int(time.time())
            filename = f"audio_{timestamp}{os.path.splitext(file.filename)[1]}"
            temp_path = os.path.join(temp_dir, filename)
            file.save(temp_path)
            
            # Ses dosyasını optimize et
            optimized_path = self._optimize_audio(temp_path, temp_dir)
            
            # Ses dosyasını parçalara böl (30 saniye)
            segments = self._split_audio(optimized_path, temp_dir)
            
            if not segments:
                return None, "Ses dosyası parçalanamadı"
            
            # Her parçayı metne çevir
            transcribed_texts = []
            
            for i, segment_path in enumerate(segments, 1):
                print(f"Parça {i}/{len(segments)} işleniyor...")
                
                # Önce Whisper dene (varsa)
                text = None
                if WHISPER_AVAILABLE:
                    text = self._transcribe_with_whisper(segment_path)
                
                # Whisper başarısız olduysa veya yoksa Google dene
                if not text:
                    text = self._transcribe_with_google(segment_path)
                
                if text:
                    transcribed_texts.append(text)
                    print(f"Parça {i} metni: {text[:50]}...")
                
                # Parça dosyasını temizle
                if os.path.exists(segment_path):
                    os.remove(segment_path)
            
            if not transcribed_texts:
                return None, "Ses tanıma başarısız oldu"
            
            final_text = " ".join(transcribed_texts)
            return final_text, None
            
        except Exception as e:
            return None, f"Ses işleme hatası: {str(e)}"
            
        finally:
            # Geçici dosyaları temizle
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            if optimized_path and os.path.exists(optimized_path) and optimized_path != temp_path:
                try:
                    os.remove(optimized_path)
                except:
                    pass
    
    def _optimize_audio(self, file_path, temp_dir):
        """SpeechRecognition kendi optimize ediyor"""
        return file_path
    
    def _split_audio(self, file_path, temp_dir, chunk_length=30000):
        """Tek parça olarak işle (SpeechRecognition 1 dakika limit var ama yeterli)"""
        return [file_path]
    
    def _transcribe_with_whisper(self, file_path):
        """Whisper hosting'de devre dışı - sadece Google Speech API kullanıyoruz"""
        return None
    
    def _transcribe_with_google(self, file_path):
        """Google Speech API ile ses tanıma"""
        try:
            with sr.AudioFile(file_path) as source:
                # Gürültü düzeyini ayarla
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.recognizer.record(source)
                
                # Türkçe dil kodları
                lang_codes = ["tr-TR", "tr"]
                
                for lang_code in lang_codes:
                    try:
                        text = self.recognizer.recognize_google(audio_data, language=lang_code)
                        return text.strip()
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as e:
                        print(f"Google API hatası: {e}")
                        break
                
                return None
                
        except Exception as e:
            print(f"Google Speech hatası: {e}")
            return None

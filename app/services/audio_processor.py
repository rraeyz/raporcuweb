"""
Ses dosyası işleme servisi - Google Speech API
"""
import os
import tempfile
import wave
import logging
from flask import current_app
import speech_recognition as sr

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

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
            
            # Ses dosyasını optimize et (WebM → WAV dönüşümü)
            optimized_path = self._optimize_audio(temp_path, temp_dir)
            
            if not optimized_path:
                return None, "Ses dosyası formatı desteklenmiyor. Lütfen WAV veya FLAC kullanın."
            
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
        """
        WebM/MP3/M4A dosyasını WAV'a çevir (SpeechRecognition için gerekli)
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Zaten WAV/FLAC/AIFF ise değiştirme
        if file_ext in ['.wav', '.flac', '.aiff']:
            return file_path
        
        # Pydub yoksa dönüşüm yapılamaz
        if not PYDUB_AVAILABLE:
            logger.error("pydub kütüphanesi bulunamadı, WebM dönüşümü yapılamıyor")
            return None
        
        try:
            # WebM/MP3/M4A → WAV dönüşümü
            logger.info(f"{file_ext} dosyası WAV'a çevriliyor ve optimize ediliyor...")
            audio = AudioSegment.from_file(file_path)
            
            # Ses optimizasyonları
            # 1. Normalize - Ses seviyesini ayarla (fazla sessizse yükselt)
            if audio.dBFS < -30:  # Çok sessiz
                audio = audio + (abs(audio.dBFS) - 20)  # -20 dBFS'ye çek
                logger.info("Ses seviyesi normalize edildi")
            
            # 2. Mono'ya çevir (stereo gereksiz)
            if audio.channels > 1:
                audio = audio.set_channels(1)
                logger.info("Stereo → Mono dönüşümü")
            
            # 3. Sample rate'i 16kHz'e ayarla (Google Speech API için optimal)
            if audio.frame_rate != 16000:
                audio = audio.set_frame_rate(16000)
                logger.info(f"Sample rate {audio.frame_rate}Hz → 16000Hz")
            
            # WAV olarak kaydet
            wav_path = os.path.join(temp_dir, f"optimized_{os.path.basename(file_path)}.wav")
            audio.export(wav_path, format="wav")
            
            logger.info(f"Dönüşüm ve optimizasyon başarılı: {wav_path}")
            return wav_path
            
        except Exception as e:
            logger.error(f"Ses dönüşüm hatası: {e}")
            return None
    
    def _split_audio(self, file_path, temp_dir, chunk_length=30000):
        """
        Uzun ses dosyalarını 30 saniyelik parçalara böl
        (Google Speech API free tier için optimum)
        """
        if not PYDUB_AVAILABLE:
            logger.warning("pydub yok, parçalama yapılamıyor")
            return [file_path]
        
        try:
            # Ses dosyasını yükle
            audio = AudioSegment.from_file(file_path)
            duration_ms = len(audio)
            
            # 30 saniyeden kısaysa parçalama
            if duration_ms <= chunk_length:
                logger.info(f"Ses dosyası {duration_ms/1000:.1f} saniye, parçalamaya gerek yok")
                return [file_path]
            
            # Parçalara böl
            segments = []
            for i, start_ms in enumerate(range(0, duration_ms, chunk_length)):
                end_ms = min(start_ms + chunk_length, duration_ms)
                chunk = audio[start_ms:end_ms]
                
                # Parça dosyası oluştur
                chunk_filename = f"chunk_{i}_{os.path.basename(file_path)}"
                chunk_path = os.path.join(temp_dir, chunk_filename)
                chunk.export(chunk_path, format="wav", parameters=["-ar", "16000", "-ac", "1"])
                
                segments.append(chunk_path)
                logger.info(f"Parça {i+1} oluşturuldu: {(end_ms-start_ms)/1000:.1f} saniye")
            
            logger.info(f"Toplam {len(segments)} parçaya bölündü")
            return segments
            
        except Exception as e:
            logger.error(f"Ses parçalama hatası: {e}")
            return [file_path]  # Hata durumunda orjinal dosya
    
    def _transcribe_with_whisper(self, file_path):
        """Whisper hosting'de devre dışı - sadece Google Speech API kullanıyoruz"""
        return None
    
    def _transcribe_with_google(self, file_path):
        """Google Speech API ile ses tanıma - WAV/FLAC destekli"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # AudioFile sadece WAV, AIFF, FLAC destekler
            if file_ext not in ['.wav', '.flac', '.aiff']:
                logger.error(f"Format {file_ext} desteklenmiyor. SpeechRecognition sadece WAV/FLAC/AIFF kabul eder.")
                return None
            
            with sr.AudioFile(file_path) as source:
                # Gürültü düzeyini ayarla
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.recognizer.record(source)
                
            # Türkçe dil kodları
            lang_codes = ["tr-TR", "tr"]
            
            for lang_code in lang_codes:
                try:
                    text = self.recognizer.recognize_google(audio_data, language=lang_code)
                    if text and text.strip():
                        logger.info(f"Ses başarıyla tanındı: {text[:50]}...")
                        return text.strip()
                except sr.UnknownValueError:
                    logger.warning(f"Ses tanınamadı: {lang_code}")
                    continue
                except sr.RequestError as e:
                    logger.error(f"Google API hatası: {e}")
                    break
            
            return None
            
        except Exception as e:
            logger.error(f"Google Speech hatası: {e}")
            return None

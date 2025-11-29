"""
Ses dosyası işleme servisi - Whisper ve Google Speech API desteği
"""
import os
import tempfile
from flask import current_app
from pydub import AudioSegment
import speech_recognition as sr

# Whisper modülünü opsiyonel olarak içe aktar
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Whisper modülü bulunamadı. Google Speech API kullanılacak.")

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
        """Ses dosyasını Speech Recognition için optimize eder"""
        try:
            audio = AudioSegment.from_file(file_path)
            
            # Normalize et
            normalized = audio.normalize()
            
            # 16000 Hz'e dönüştür (optimal)
            if audio.frame_rate != 16000:
                normalized = normalized.set_frame_rate(16000)
            
            # Mono'ya çevir
            if audio.channels > 1:
                normalized = normalized.set_channels(1)
            
            # WAV formatında kaydet
            output_path = os.path.join(temp_dir, f"optimized_{os.path.basename(file_path)}.wav")
            normalized.export(output_path, format="wav")
            
            return output_path
            
        except Exception as e:
            print(f"Ses optimizasyonu hatası: {e}")
            return file_path
    
    def _split_audio(self, file_path, temp_dir, chunk_length=30000):
        """Ses dosyasını 30 saniyelik parçalara böler"""
        try:
            audio = AudioSegment.from_file(file_path)
            segments = []
            
            for i in range(0, len(audio), chunk_length):
                chunk = audio[i:i + chunk_length]
                segment_path = os.path.join(temp_dir, f"segment_{i//chunk_length}.wav")
                chunk.export(segment_path, format="wav")
                segments.append(segment_path)
            
            return segments
            
        except Exception as e:
            print(f"Ses parçalama hatası: {e}")
            return []
    
    def _transcribe_with_whisper(self, file_path):
        """Whisper ile ses tanıma"""
        try:
            if not WHISPER_AVAILABLE:
                return None
            
            # Model ilk kulanımda yüklenir (lazy loading)
            if self.whisper_model is None:
                print("Whisper modeli yükleniyor...")
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                model_dir = os.path.join(upload_folder, 'models')
                os.makedirs(model_dir, exist_ok=True)
                self.whisper_model = whisper.load_model("base", download_root=model_dir)
            
            result = self.whisper_model.transcribe(
                file_path,
                language="tr",
                fp16=False,
                temperature=0,
                best_of=1,
                beam_size=1
            )
            
            return result["text"].strip()
            
        except Exception as e:
            print(f"Whisper hatası: {e}")
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

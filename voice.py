import os
import asyncio
import logging
from datetime import datetime
import hashlib
import random
import tempfile
import subprocess

logger = logging.getLogger(__name__)

class VoiceManager:
    def __init__(self):
        self.cache_dir = "voice_cache"
        self._ensure_cache_dir()
        self.memory_cache = {}
        self.max_cache_size = 100
        
        # Проверяем наличие ffmpeg
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, 
                         check=True)
            return True
        except:
            logger.warning("ffmpeg not found, using MP3 format")
            return False
    
    def _ensure_cache_dir(self):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_key(self, text, lang='en'):
        key_string = f"{text}_{lang}_{random.randint(1,100)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key):
        return os.path.join(self.cache_dir, f"{cache_key}")
    
    async def text_to_speech(self, text, lang='en', slow=False):
        try:
            cache_key = self._get_cache_key(text, lang)
            
            # Проверяем кэш
            for ext in ['.ogg', '.mp3']:
                cache_path = os.path.join(self.cache_dir, f"{cache_key}{ext}")
                if os.path.exists(cache_path):
                    logger.info(f"Voice cache hit: {cache_key}")
                    return cache_path
            
            from gtts import gTTS
            
            # Создаем временный MP3 файл
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_mp3 = tmp_file.name
            
            # Генерируем MP3
            tts = gTTS(text=text, lang=lang, slow=slow)
            tts.save(tmp_mp3)
            
            # Пытаемся конвертировать в OGG, если есть ffmpeg
            if self.ffmpeg_available:
                try:
                    ogg_path = os.path.join(self.cache_dir, f"{cache_key}.ogg")
                    cmd = ['ffmpeg', '-i', tmp_mp3, '-c:a', 'libopus', '-b:a', '24k', '-y', ogg_path]
                    subprocess.run(cmd, capture_output=True, check=True)
                    os.unlink(tmp_mp3)
                    
                    if os.path.exists(ogg_path):
                        self.memory_cache[cache_key] = ogg_path
                        logger.info(f"Voice generated as OGG: {cache_key}")
                        return ogg_path
                except:
                    logger.warning("FFmpeg conversion failed, using MP3")
            
            # Если нет ffmpeg или конвертация не удалась, используем MP3
            mp3_path = os.path.join(self.cache_dir, f"{cache_key}.mp3")
            os.rename(tmp_mp3, mp3_path)
            
            self.memory_cache[cache_key] = mp3_path
            logger.info(f"Voice generated as MP3: {cache_key}")
            return mp3_path
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None
    
    async def cleanup_old_cache(self, max_age_hours=24):
        try:
            now = datetime.now()
            deleted = 0
            
            for filename in os.listdir(self.cache_dir):
                filepath = os.path.join(self.cache_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                
                if (now - file_time).total_seconds() > max_age_hours * 3600:
                    os.remove(filepath)
                    deleted += 1
            
            logger.info(f"Cleaned up {deleted} old voice files")
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

voice_manager = VoiceManager()

async def periodic_cache_cleanup():
    while True:
        await asyncio.sleep(3600)
        await voice_manager.cleanup_old_cache(max_age_hours=48)
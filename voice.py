import os
import asyncio
import aiofiles
from gtts import gTTS
from pydub import AudioSegment
import io
import logging
from datetime import datetime
import hashlib
import random

logger = logging.getLogger(__name__)

class VoiceManager:
    def __init__(self):
        self.cache_dir = "voice_cache"
        self._ensure_cache_dir()
        
        self.voices = {
            'en': {'tld': 'com', 'slow': False},
            'en-uk': {'tld': 'co.uk', 'slow': False},
            'en-au': {'tld': 'com.au', 'slow': False}
        }
        
        self.memory_cache = {}
        self.max_cache_size = 100
    
    def _ensure_cache_dir(self):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_key(self, text, lang='en'):
        key_string = f"{text}_{lang}_{random.randint(1,100)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key):
        return os.path.join(self.cache_dir, f"{cache_key}.ogg")
    
    async def text_to_speech(self, text, lang='en', slow=False):
        try:
            cache_key = self._get_cache_key(text, lang)
            cache_path = self._get_cache_path(cache_key)
            
            if os.path.exists(cache_path):
                logger.info(f"Voice cache hit: {cache_key}")
                return cache_path
            
            tts = gTTS(text=text, lang=lang, slow=slow)
            
            mp3_fp = io.BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            
            audio = AudioSegment.from_mp3(mp3_fp)
            audio = audio.normalize()
            
            audio.export(cache_path, format='ogg', codec='libopus')
            
            if len(self.memory_cache) >= self.max_cache_size:
                oldest = next(iter(self.memory_cache))
                del self.memory_cache[oldest]
            
            self.memory_cache[cache_key] = cache_path
            
            logger.info(f"Voice generated: {cache_key}")
            return cache_path
            
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
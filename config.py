import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    DATABASE_URL = os.getenv('DATABASE_URL')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL')
    PORT = int(os.getenv('PORT', 8080))
    
    # Настройки обучения
    DEFAULT_WORDS_PER_DAY = 10
    SRS_STAGES = [0, 1, 3, 7, 14, 30]
    MAX_STAGE = 5
    
    # Уровни
    LEVELS = {
        'A1': {'name': 'Начинающий', 'words': 500},
        'A2': {'name': 'Элементарный', 'words': 1000},
        'B1': {'name': 'Средний', 'words': 2000},
        'B2': {'name': 'Выше среднего', 'words': 4000},
        'C1': {'name': 'Продвинутый', 'words': 8000}
    }
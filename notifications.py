import asyncio
from datetime import datetime
from celery import Celery
from config import Config

celery_app = Celery(
    'wordich',
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL
)

@celery_app.task
def send_daily_notifications():
    asyncio.run(_send_notifications())

async def _send_notifications():
    from database import Database
    from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
    
    db = Database()
    bot = Bot(token=Config.BOT_TOKEN)
    
    session = db.get_session()
    try:
        users = session.query(User).filter_by(notification_enabled=True).all()
        
        current_time = datetime.utcnow().strftime('%H:%M')
        
        for user in users:
            if user.notification_time == current_time:
                try:
                    due_words = session.query(UserWordProgress).filter(
                        UserWordProgress.user_id == user.id,
                        UserWordProgress.next_review <= datetime.utcnow()
                    ).count()
                    
                    if due_words > 0:
                        text = f"🔔 *Время учить слова!*\n\n"
                        text += f"У тебя {due_words} слов для повторения сегодня."
                        
                        keyboard = [[InlineKeyboardButton("📚 Начать урок", callback_data="learn_today")]]
                        
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=text,
                            parse_mode='Markdown',
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                except Exception as e:
                    print(f"Error sending notification: {e}")
    finally:
        session.close()
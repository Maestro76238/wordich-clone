import logging
import os
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from aiohttp import web
import threading

from config import Config
from handlers import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Простая функция для обработки веб-запросов (health check)
async def handle(request):
    return web.Response(text="I'm alive!")

def run_web_server():
    """Запускает простой веб-сервер на порту PORT."""
    app = web.Application()
    app.router.add_get('/', handle)
    app.router.add_get('/health', handle)  # Render может проверять этот путь
    
    port = int(os.environ.get('PORT', 8080))
    web.run_app(app, host='0.0.0.0', port=port)

def main():
    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    logging.info(f"Web server started on port {os.environ.get('PORT', 8080)}")

    # ✅ ИСПРАВЛЕНО: Правильный способ создания Updater
    # Вместо token= используем первую позицию или аргумент 'token' без use_context
    updater = Updater(Config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Добавляем все обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(level_callback, pattern="^level_"))
    dp.add_handler(CallbackQueryHandler(learn_today, pattern="^learn_today$"))
    dp.add_handler(CallbackQueryHandler(stats, pattern="^stats$"))
    dp.add_handler(CallbackQueryHandler(settings, pattern="^settings$"))
    dp.add_handler(CallbackQueryHandler(achievements, pattern="^achievements$"))
    dp.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    dp.add_handler(CallbackQueryHandler(change_daily, pattern="^change_daily$"))
    dp.add_handler(CallbackQueryHandler(set_daily, pattern="^set_daily_"))
    dp.add_handler(CallbackQueryHandler(toggle_audio, pattern="^toggle_audio$"))
    dp.add_handler(CallbackQueryHandler(word_callback, pattern="^(know_|dont_know_|example_|skip_|audio_|audiotest_)"))
    dp.add_handler(CallbackQueryHandler(test_answer, pattern="^test_answer_"))

    logging.info("Bot starting in polling mode...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
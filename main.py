import logging
import os
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from flask import Flask
import threading

from config import Config
from handlers import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Создаем простое Flask приложение для health check
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def main():
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info(f"Flask server started on port {os.environ.get('PORT', 8080)}")
    
    # ✅ Правильный способ создания Updater
    updater = Updater(token=Config.BOT_TOKEN, use_context=False)
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
import logging
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from config import Config
from handlers import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    # Создаем Updater без webhook
    updater = Updater(token=Config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Добавляем обработчики
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

    # Запускаем polling (простой режим)
    print("Бот запускается в режиме polling...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
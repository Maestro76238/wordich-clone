import logging
import os
import asyncio
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from aiohttp import web
from threading import Thread
from config import Config
from handlers import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Простой веб-сервер для Render
async def handle(request):
    return web.Response(text="Bot is running!")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    app.router.add_get('/health', handle)
    
    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Web server started on port {port}")
    
    # Держим сервер запущенным
    await asyncio.Event().wait()

def start_web_server():
    """Запуск веб-сервера в отдельном потоке"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_web_server())

def main():
    # Запускаем веб-сервер в отдельном потоке
    web_thread = Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    # ✅ УБИРАЕМ use_context - он больше не нужен
    updater = Updater(Config.BOT_TOKEN)
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
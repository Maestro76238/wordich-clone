import logging
import os
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PicklePersistence
)
from aiohttp import web
from telegram import Update

from config import Config
from handlers import *
from voice import periodic_cache_cleanup

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def health(request):
    return web.Response(text="OK")

async def webhook_handler(request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return web.Response(text="OK")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(status=500)

async def post_init(application):
    if Config.WEBHOOK_URL:
        await application.bot.set_webhook(
            url=f"{Config.WEBHOOK_URL}/webhook",
            allowed_updates=['message', 'callback_query']
        )
        logger.info(f"Webhook set to {Config.WEBHOOK_URL}/webhook")
    
    asyncio.create_task(periodic_cache_cleanup())

def main():
    global application
    
    persistence = PicklePersistence(filepath="wordich.persist")
    
    application = (
        Application.builder()
        .token(Config.BOT_TOKEN)
        .persistence(persistence)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(level_callback, pattern="^level_"))
    application.add_handler(CallbackQueryHandler(learn_today, pattern="^learn_today$"))
    application.add_handler(CallbackQueryHandler(stats, pattern="^stats$"))
    application.add_handler(CallbackQueryHandler(settings, pattern="^settings$"))
    application.add_handler(CallbackQueryHandler(achievements, pattern="^achievements$"))
    application.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(change_daily, pattern="^change_daily$"))
    application.add_handler(CallbackQueryHandler(set_daily, pattern="^set_daily_"))
    application.add_handler(CallbackQueryHandler(toggle_audio, pattern="^toggle_audio$"))
    application.add_handler(CallbackQueryHandler(word_callback, pattern="^(know_|dont_know_|example_|skip_|audio_|audiotest_)"))
    application.add_handler(CallbackQueryHandler(test_answer, pattern="^test_answer_"))

    if Config.WEBHOOK_URL:
        app = web.Application()
        app.router.add_get('/health', health)
        app.router.add_post('/webhook', webhook_handler)
        
        web.run_app(
            app,
            host='0.0.0.0',
            port=Config.PORT
        )
    else:
        application.run_polling()

if __name__ == "__main__":
    main()
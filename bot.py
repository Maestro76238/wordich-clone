import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import random

from database import Database
from utils import QuizGenerator

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = Database()
quiz_gen = QuizGenerator()

# Константы
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 8080))

# Состояния пользователей (для хранения временных данных)
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Проверяем, есть ли пользователь в БД
    db_user = db.get_user(user.id)
    if not db_user:
        db.create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        welcome_text = f"👋 Привет, {user.first_name}! Я помогу тебе учить английские слова."
    else:
        welcome_text = f"👋 С возвращением, {user.first_name}!"
    
    welcome_text += """
    
📚 Я использую метод интервальных повторений, чтобы слова запоминались надолго.

🔹 Каждый день я буду присылать 10 новых слов
🔹 Буду напоминать о повторении в оптимальное время
🔹 Проведу тесты для закрепления материала

Выбери свой уровень:"""
    
    keyboard = [
        [
            InlineKeyboardButton("🌱 A1 (Начинающий)", callback_data="level_A1"),
            InlineKeyboardButton("🌿 A2 (Элементарный)", callback_data="level_A2")
        ],
        [
            InlineKeyboardButton("🍃 B1 (Средний)", callback_data="level_B1"),
            InlineKeyboardButton("🌳 B2 (Выше среднего)", callback_data="level_B2")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def level_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора уровня"""
    query = update.callback_query
    await query.answer()
    
    level = query.data.replace("level_", "")
    user_id = update.effective_user.id
    
    # Обновляем уровень пользователя в БД
    session = db.get_session()
    try:
        user = session.query(db.User).filter_by(telegram_id=user_id).first()
        if user:
            user.level = level
            session.commit()
    finally:
        session.close()
    
    keyboard = [
        [InlineKeyboardButton("📚 Учить слова сегодня", callback_data="learn_today")],
        [InlineKeyboardButton("📊 Мой прогресс", callback_data="progress")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"Отлично! Выбран уровень {level}.\n\n"
        "Теперь можно начинать обучение. Что хочешь сделать?",
        reply_markup=reply_markup
    )

async def learn_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать ежедневный урок"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db_user = db.get_user(user_id)
    
    if not db_user:
        await query.edit_message_text("Сначала запусти бота командой /start")
        return
    
    # Получаем слова для сегодняшнего урока
    words = db.get_daily_words(db_user.id, db_user.daily_words)
    
    if not words:
        await query.edit_message_text(
            "🎉 Поздравляю! Ты выучил все доступные слова!\n"
            "Скоро я добавлю новые."
        )
        return
    
    # Сохраняем слова в сессию пользователя
    user_sessions[user_id] = {
        'words': words,
        'current_index': 0,
        'correct': 0,
        'total': len(words)
    }
    
    await send_next_word(query, user_id)

async def send_next_word(query, user_id):
    """Отправить следующее слово для изучения"""
    session = user_sessions.get(user_id)
    if not session:
        return
    
    idx = session['current_index']
    words = session['words']
    
    if idx >= len(words):
        # Урок завершен
        correct = session['correct']
        total = session['total']
        percentage = (correct / total) * 100
        
        keyboard = [
            [InlineKeyboardButton("📚 Следующий урок", callback_data="learn_today")],
            [InlineKeyboardButton("📊 Прогресс", callback_data="progress")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎉 Урок завершен!\n\n"
            f"Правильных ответов: {correct} из {total}\n"
            f"Точность: {percentage:.1f}%\n\n"
            f"Так держать! Возвращайся завтра за новой порцией слов.",
            reply_markup=reply_markup
        )
        return
    
    word = words[idx]
    
    # Генерируем тест (случайный тип)
    test_type = random.choice(['translation', 'word', 'fill'])
    
    if test_type == 'translation':
        # Получаем неправильные варианты из других слов
        other_words = [w for w in words if w.id != word.id]
        wrong = [w.translation for w in other_words[:3]]
        quiz = quiz_gen.generate_translation_quiz(word.word, word.translation, wrong)
        
        keyboard = []
        for option in quiz['options']:
            keyboard.append([InlineKeyboardButton(
                option, 
                callback_data=f"answer_{word.id}_{option}_{word.translation}"
            )])
        
    elif test_type == 'word':
        other_words = [w for w in words if w.id != word.id]
        wrong = [w.word for w in other_words[:3]]
        quiz = quiz_gen.generate_word_quiz(word.translation, word.word, wrong)
        
        keyboard = []
        for option in quiz['options']:
            keyboard.append([InlineKeyboardButton(
                option, 
                callback_data=f"answer_{word.id}_{option}_{word.word}"
            )])
    
    else:  # fill
        quiz = quiz_gen.generate_fill_blank_quiz(word.example, word.word)
        
        # Для fill-теста просто показываем вопрос и ждем текстовый ответ
        context = {
            'user_id': user_id,
            'word_id': word.id,
            'correct_answer': word.word
        }
        
        # Сохраняем контекст для обработки текстового ответа
        user_sessions[user_id]['awaiting_answer'] = context
        
        await query.edit_message_text(
            f"📝 *{quiz['question']}*\n\n"
            f"Подсказка: {word.translation}\n"
            f"Напиши правильное слово:",
            parse_mode='Markdown'
        )
        return
    
    # Добавляем кнопки навигации
    keyboard.append([InlineKeyboardButton("⏭ Пропустить", callback_data=f"skip_{word.id}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = f"📚 Слово {idx + 1} из {session['total']}\n\n"
    message += f"*{quiz['question']}*"
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ответов на тесты"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    action = data[0]
    
    if action == 'skip':
        word_id = int(data[1])
        user_id = update.effective_user.id
        
        # Пропускаем слово (считаем неправильным)
        if user_id in user_sessions:
            db.update_word_progress(
                db.get_user(user_id).id,
                word_id,
                False
            )
            user_sessions[user_id]['current_index'] += 1
            await send_next_word(query, user_id)
    
    elif action == 'answer':
        word_id = int(data[1])
        answer = data[2]
        correct = data[3]
        user_id = update.effective_user.id
        
        is_correct = (answer == correct)
        
        # Обновляем прогресс в БД
        if user_id in user_sessions:
            db_user = db.get_user(user_id)
            db.update_word_progress(db_user.id, word_id, is_correct)
            
            if is_correct:
                user_sessions[user_id]['correct'] += 1
                feedback = "✅ Правильно! Молодец!"
            else:
                feedback = f"❌ Неправильно. Правильный ответ: {correct}"
            
            user_sessions[user_id]['current_index'] += 1
            
            # Показываем пример использования
            session = db.get_session()
            try:
                word = session.query(db.Word).get(word_id)
                if word and word.example:
                    feedback += f"\n\n📝 *Пример:*\n{word.example}\n{word.example_translation}"
            finally:
                session.close()
            
            await query.edit_message_text(feedback, parse_mode='Markdown')
            
            # Небольшая пауза перед следующим словом
            await asyncio.sleep(2)
            await send_next_word(query, user_id)

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений (для fill-тестов)"""
    user_id = update.effective_user.id
    text = update.message.text.strip().lower()
    
    if user_id in user_sessions and 'awaiting_answer' in user_sessions[user_id]:
        context_data = user_sessions[user_id].pop('awaiting_answer')
        correct = context_data['correct_answer'].lower()
        
        is_correct = (text == correct)
        
        # Обновляем прогресс
        db_user = db.get_user(user_id)
        db.update_word_progress(db_user.id, context_data['word_id'], is_correct)
        
        if is_correct:
            user_sessions[user_id]['correct'] += 1
            feedback = "✅ Правильно! Молодец!"
        else:
            feedback = f"❌ Неправильно. Правильный ответ: {correct}"
        
        user_sessions[user_id]['current_index'] += 1
        
        # Получаем пример для показа
        session = db.get_session()
        try:
            word = session.query(db.Word).get(context_data['word_id'])
            if word and word.example:
                feedback += f"\n\n📝 *Пример:*\n{word.example}\n{word.example_translation}"
        finally:
            session.close()
        
        await update.message.reply_text(feedback, parse_mode='Markdown')
        
        # Продолжаем урок
        await asyncio.sleep(2)
        
        # Создаем фиктивный query для send_next_word
        class FakeQuery:
            def __init__(self, user_id):
                self.user_id = user_id
            async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        
        await send_next_word(FakeQuery(user_id), user_id)
    else:
        await update.message.reply_text(
            "Используй команду /start для начала работы или кнопки меню."
        )

async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать прогресс пользователя"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db_user = db.get_user(user_id)
    
    if not db_user:
        await query.edit_message_text("Сначала запусти бота командой /start")
        return
    
    session = db.get_session()
    try:
        # Статистика по словам
        total_words = session.query(db.Word).count()
        learned = session.query(db.UserWordProgress).filter_by(
            user_id=db_user.id
        ).count()
        
        stage_counts = session.query(
            db.UserWordProgress.stage,
            db.func.count(db.UserWordProgress.id)
        ).filter_by(
            user_id=db_user.id
        ).group_by(db.UserWordProgress.stage).all()
        
        progress_text = f"📊 *Твой прогресс*\n\n"
        progress_text += f"🔥 Текущая серия: {db_user.streak} дней\n"
        progress_text += f"📚 Всего слов в базе: {total_words}\n"
        progress_text += f"✅ Изучено слов: {learned}\n\n"
        
        progress_text += "*Уровни запоминания:*\n"
        for stage, count in stage_counts:
            stage_names = ['Новые', 'Начальный', 'Закрепление', 'Уверенный', 'Хороший', 'Отличный']
            progress_text += f"  {stage_names[stage]}: {count} слов\n"
        
        # Рассчитываем прогресс до следующего уровня
        if learned > 0:
            next_level_words = {
                'A1': 100,
                'A2': 300,
                'B1': 600,
                'B2': 1200
            }
            target = next_level_words.get(db_user.level, 100)
            progress_percent = min(100, (learned / target) * 100)
            progress_text += f"\n🎯 Прогресс к уровню {db_user.level}: {progress_percent:.1f}%"
        
    finally:
        session.close()
    
    keyboard = [
        [InlineKeyboardButton("📚 Продолжить урок", callback_data="learn_today")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        progress_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройки пользователя"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db_user = db.get_user(user_id)
    
    if not db_user:
        await query.edit_message_text("Сначала запусти бота командой /start")
        return
    
    keyboard = [
        [InlineKeyboardButton(f"📊 Слов в день: {db_user.daily_words}", callback_data="change_daily")],
        [InlineKeyboardButton(f"🎯 Уровень: {db_user.level}", callback_data="change_level")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚙️ *Настройки*\n\n"
        "Здесь ты можешь изменить параметры обучения:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📚 Учить слова сегодня", callback_data="learn_today")],
        [InlineKeyboardButton("📊 Мой прогресс", callback_data="progress")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🏠 *Главное меню*\n\n"
        "Выбери, что хочешь сделать:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def health_check(request):
    """Эндпоинт для проверки здоровья (требуется Render)"""
    return web.Response(text="OK")

async def post_init(application: Application):
    """Настройка webhook после инициализации"""
    if WEBHOOK_URL:
        await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

def main():
    """Главная функция"""
    # Создаем приложение
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(level_callback, pattern="^level_"))
    application.add_handler(CallbackQueryHandler(learn_today, pattern="^learn_today$"))
    application.add_handler(CallbackQueryHandler(progress, pattern="^progress$"))
    application.add_handler(CallbackQueryHandler(settings, pattern="^settings$"))
    application.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(answer_callback, pattern="^(skip_|answer_)"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    # Запуск бота
    if WEBHOOK_URL:
        # Режим webhook для продакшна
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="webhook",
            webhook_url=f"{WEBHOOK_URL}/webhook"
        )
    else:
        # Режим polling для локальной разработки
        application.run_polling()

if __name__ == "__main__":
    main()
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import random
import asyncio
import os

from database import Database
from quiz import QuizGenerator
from keyboards import Keyboards
from voice import voice_manager
from config import Config

logger = logging.getLogger(__name__)
db = Database()
quiz_gen = QuizGenerator()

user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    db_user = db.get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    welcome = f"""
🎯 *Wordich Clone - твой личный репетитор английского*

Привет, {user.first_name}! Я помогу тебе выучить тысячи английских слов с помощью научного метода интервальных повторений.

📊 *Твоя статистика:*
• Уровень: {db_user.level}
• Слов в день: {db_user.daily_words}
• Текущая серия: {db_user.streak} дней
• Аудио: {'✅' if db_user.audio_enabled else '❌'}

Выбери свой уровень для начала:"""
    
    await update.message.reply_text(
        welcome,
        reply_markup=Keyboards.level_selection(),
        parse_mode='Markdown'
    )

async def level_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    level = query.data.replace("level_", "")
    user_id = update.effective_user.id
    
    session = db.get_session()
    try:
        user = session.query(db.User).filter_by(telegram_id=user_id).first()
        if user:
            user.level = level
            session.commit()
    finally:
        session.close()
    
    await query.edit_message_text(
        f"✅ Уровень {level} выбран!\n\n"
        f"Теперь ты готов начать обучение. Каждый день я буду присылать "
        f"тебе {Config.DEFAULT_WORDS_PER_DAY} новых слов и напоминать о повторении.\n\n"
        f"🔊 У тебя {'включены' if db_user.audio_enabled else 'выключены'} голосовые сообщения. "
        f"Их можно настроить в меню.",
        reply_markup=Keyboards.main_menu()
    )

async def learn_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db_user = db.get_or_create_user(user_id)
    
    words = db.get_daily_words(db_user.id)
    
    if not words:
        await query.edit_message_text(
            "🎉 Поздравляю! Ты выучил все доступные слова!\n"
            "Скоро я добавлю новые уровни.",
            reply_markup=Keyboards.main_menu()
        )
        return
    
    user_sessions[user_id] = {
        'words': words,
        'current_index': 0,
        'correct': 0,
        'total': len(words),
        'start_time': datetime.utcnow()
    }
    
    await send_word(query, user_id, context)

async def send_word(query, user_id, context):
    session = user_sessions.get(user_id)
    if not session:
        return
    
    idx = session['current_index']
    words = session['words']
    
    if idx >= len(words):
        await finish_lesson(query, user_id)
        return
    
    word = words[idx]
    
    db_user = db.get_or_create_user(user_id)
    
    text = f"📚 *Слово {idx + 1} из {session['total']}*\n\n"
    text += f"*{word.word}*"
    if word.transcription:
        text += f"  [{word.transcription}]"
    text += f"\n\n_{word.translation}_"
    
    await query.edit_message_text(
        text,
        reply_markup=Keyboards.learning_options(word.id, db_user.audio_enabled),
        parse_mode='Markdown'
    )

async def word_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    action = data[0]
    word_id = int(data[1])
    user_id = update.effective_user.id
    
    if user_id not in user_sessions:
        await query.edit_message_text("Сессия истекла. Начни заново.")
        return
    
    session = user_sessions[user_id]
    db_user = db.get_or_create_user(user_id)
    
    word = next((w for w in session['words'] if w.id == word_id), None)
    if not word:
        await query.edit_message_text("Ошибка: слово не найдено")
        return
    
    # АУДИО: Озвучить слово
    if action == 'audio':
        await query.edit_message_text("🔊 Генерирую аудио...")
        
        audio_path = await voice_manager.text_to_speech(word.word)
        
        if audio_path and os.path.exists(audio_path):
            with open(audio_path, 'rb') as audio_file:
                await context.bot.send_voice(
                    chat_id=user_id,
                    voice=audio_file,
                    caption=f"Слово: {word.word}",
                    reply_markup=Keyboards.learning_options(word_id, db_user.audio_enabled)
                )
            await query.delete_message()
        else:
            await query.edit_message_text(
                "❌ Не удалось озвучить слово",
                reply_markup=Keyboards.learning_options(word_id, db_user.audio_enabled)
            )
        return
    
    # АУДИО-ТЕСТ
    elif action == 'audiotest':
        await query.edit_message_text("🎧 Генерирую аудио-тест...")
        
        audio_path = await voice_manager.text_to_speech(word.word)
        
        other_words = [w for w in session['words'] if w.id != word.id]
        wrong_options = [w.translation for w in other_words[:3]]
        while len(wrong_options) < 3:
            wrong_options.append(f"вариант_{random.randint(1, 100)}")
        
        options = [word.translation] + wrong_options
        random.shuffle(options)
        
        context.user_data['current_test'] = {
            'word_id': word_id,
            'correct': word.translation,
            'options': options
        }
        
        keyboard = []
        for i, option in enumerate(options):
            keyboard.append([InlineKeyboardButton(option, callback_data=f"test_answer_{i}")])
        
        if audio_path and os.path.exists(audio_path):
            with open(audio_path, 'rb') as audio_file:
                await context.bot.send_voice(
                    chat_id=user_id,
                    voice=audio_file,
                    caption="🎧 Какое это слово?",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            await query.delete_message()
        else:
            await query.edit_message_text(
                "❌ Не удалось создать аудио-тест",
                reply_markup=Keyboards.learning_options(word_id, db_user.audio_enabled)
            )
        return
    
    # ПРИМЕР С АУДИО
    elif action == 'example':
        if word and word.example:
            text = f"📝 *Пример со словом {word.word}:*\n\n"
            text += f"{word.example}\n\n_{word.example_translation}_"
            
            await query.edit_message_text(
                text,
                parse_mode='Markdown'
            )
            
            if db_user.audio_enabled:
                audio_path = await voice_manager.text_to_speech(word.example)
                if audio_path and os.path.exists(audio_path):
                    await asyncio.sleep(1)
                    with open(audio_path, 'rb') as audio_file:
                        await context.bot.send_voice(
                            chat_id=user_id,
                            voice=audio_file,
                            caption="🔊 Пример произношения"
                        )
            
            await asyncio.sleep(2)
            await send_word(query, user_id, context)
        return
    
    # ОБЫЧНЫЕ ОТВЕТЫ
    elif action == 'know':
        correct = True
        session['correct'] += 1
        feedback = "✅ Отлично! Запоминаем."
        
    elif action == 'dont_know':
        correct = False
        feedback = "❌ Ничего страшного, продолжим учить."
        
    elif action == 'skip':
        correct = False
        feedback = "⏭ Пропускаем..."
    
    else:
        return
    
    db.update_word_progress(db_user.id, word_id, correct)
    
    session['current_index'] += 1
    
    await query.edit_message_text(feedback, parse_mode='Markdown')
    
    await asyncio.sleep(1.5)
    await send_word(query, user_id, context)

async def test_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    answer_index = int(query.data.replace("test_answer_", ""))
    test_data = context.user_data.get('current_test', {})
    
    if not test_data:
        await query.edit_message_text("Тест устарел. Начни заново.")
        return
    
    selected = test_data['options'][answer_index]
    correct = test_data['correct']
    word_id = test_data['word_id']
    user_id = update.effective_user.id
    
    is_correct = (selected == correct)
    
    db_user = db.get_or_create_user(user_id)
    db.update_word_progress(db_user.id, word_id, is_correct)
    
    if is_correct and user_id in user_sessions:
        user_sessions[user_id]['correct'] += 1
        feedback = "✅ Правильно! Молодец!"
    else:
        feedback = f"❌ Неправильно. Правильный ответ: {correct}"
    
    await query.edit_message_text(feedback)
    
    await asyncio.sleep(2)
    
    if user_id in user_sessions:
        class FakeQuery:
            def __init__(self, uid):
                self.user_id = uid
            async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                await context.bot.send_message(
                    chat_id=self.user_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
        
        await send_word(FakeQuery(user_id), user_id, context)

async def finish_lesson(query, user_id):
    session = user_sessions.get(user_id)
    if not session:
        return
    
    correct = session['correct']
    total = session['total']
    accuracy = (correct / total) * 100
    time_spent = (datetime.utcnow() - session['start_time']).seconds // 60
    
    text = f"""
🎉 *Урок завершен!*

📊 *Результаты:*
• Правильно: {correct} из {total}
• Точность: {accuracy:.1f}%
• Время: {time_spent} мин

"""
    if accuracy >= 90:
        text += "🌟 Отличный результат! Так держать!"
    elif accuracy >= 70:
        text += "👍 Хорошая работа! Продолжай в том же духе!"
    else:
        text += "💪 Тренируйся еще, и результаты улучшатся!"
    
    del user_sessions[user_id]
    
    await query.edit_message_text(
        text,
        reply_markup=Keyboards.after_lesson(),
        parse_mode='Markdown'
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db_user = db.get_or_create_user(user_id)
    
    stats_data = db.get_user_stats(db_user.id)
    if not stats_data:
        await query.edit_message_text("Статистика пока недоступна")
        return
    
    text = f"""
📊 *Твоя статистика*

🔥 *Серия:* {stats_data['user'].streak} дней
🎯 *Точность:* {stats_data['accuracy']:.1f}%
📚 *Всего повторений:* {stats_data['stats'].total_reviews}
✅ *Правильных ответов:* {stats_data['stats'].correct_reviews}
⭐️ *Выучено слов:* {stats_data['stats'].total_words_learned}
📅 *Сегодня к повторению:* {stats_data['due_today']}

*Прогресс по уровням:*
"""
    
    for level, progress in stats_data['level_progress'].items():
        if progress['total'] > 0:
            bar = '█' * int(progress['percent'] // 10) + '░' * (10 - int(progress['percent'] // 10))
            text += f"{level}: {bar} {progress['learned']}/{progress['total']} ({progress['percent']:.0f}%)\n"
    
    await query.edit_message_text(
        text,
        reply_markup=Keyboards.main_menu(),
        parse_mode='Markdown'
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db_user = db.get_or_create_user(user_id)
    
    await query.edit_message_text(
        "⚙️ *Настройки*\n\n"
        "Здесь ты можешь изменить параметры обучения:",
        reply_markup=Keyboards.settings_menu(db_user),
        parse_mode='Markdown'
    )

async def toggle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    session = db.get_session()
    try:
        user = session.query(db.User).filter_by(telegram_id=user_id).first()
        if user:
            user.audio_enabled = not user.audio_enabled
            session.commit()
            status = "включены" if user.audio_enabled else "выключены"
            await query.edit_message_text(
                f"🔊 Голосовые сообщения {status}",
                reply_markup=Keyboards.settings_menu(user)
            )
    finally:
        session.close()

async def change_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for count in [5, 10, 15, 20, 30]:
        keyboard.append([InlineKeyboardButton(
            f"{count} слов в день", 
            callback_data=f"set_daily_{count}"
        )])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="settings")])
    
    await query.edit_message_text(
        "Выбери количество новых слов в день:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    count = int(query.data.replace("set_daily_", ""))
    user_id = update.effective_user.id
    
    session = db.get_session()
    try:
        user = session.query(db.User).filter_by(telegram_id=user_id).first()
        if user:
            user.daily_words = count
            session.commit()
    finally:
        session.close()
    
    await query.edit_message_text(
        f"✅ Установлено {count} слов в день",
        reply_markup=Keyboards.settings_menu(user)
    )

async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    db_user = db.get_or_create_user(user_id)
    stats_data = db.get_user_stats(db_user.id)
    
    achievements_list = [
        ("🔥 Новичок", "Выучить 10 слов", stats_data['stats'].total_words_learned >= 10, "⭐️"),
        ("🔥 Ученик", "Выучить 100 слов", stats_data['stats'].total_words_learned >= 100, "🌟"),
        ("🔥 Мастер", "Выучить 500 слов", stats_data['stats'].total_words_learned >= 500, "💫"),
        ("📅 Трудоголик", "Заниматься 7 дней подряд", stats_data['user'].streak >= 7, "📆"),
        ("📅 Легенда", "Заниматься 30 дней подряд", stats_data['user'].streak >= 30, "🏆"),
        ("🎯 Снайпер", "Точность 90% за неделю", stats_data['accuracy'] >= 90, "🎯"),
    ]
    
    text = "🏆 *Твои достижения*\n\n"
    
    for name, desc, unlocked, emoji in achievements_list:
        if unlocked:
            text += f"{emoji} *{name}* - {desc} ✅\n"
        else:
            text += f"🔒 {name} - {desc}\n"
    
    await query.edit_message_text(
        text,
        reply_markup=Keyboards.main_menu(),
        parse_mode='Markdown'
    )

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🏠 *Главное меню*\n\n"
        "Выбери, что хочешь сделать:",
        reply_markup=Keyboards.main_menu(),
        parse_mode='Markdown'
    )
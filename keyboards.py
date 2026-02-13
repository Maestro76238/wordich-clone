from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class Keyboards:
    @staticmethod
    def main_menu():
        keyboard = [
            [InlineKeyboardButton("📚 Учить слова", callback_data="learn_today")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")],
            [InlineKeyboardButton("🏆 Достижения", callback_data="achievements")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def level_selection():
        keyboard = [
            [
                InlineKeyboardButton("🌱 A1", callback_data="level_A1"),
                InlineKeyboardButton("🌿 A2", callback_data="level_A2")
            ],
            [
                InlineKeyboardButton("🍃 B1", callback_data="level_B1"),
                InlineKeyboardButton("🌳 B2", callback_data="level_B2")
            ],
            [
                InlineKeyboardButton("🌲 C1", callback_data="level_C1")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def learning_options(word_id, audio_enabled=True):
        keyboard = [
            [
                InlineKeyboardButton("🔊 Озвучить", callback_data=f"audio_{word_id}"),
                InlineKeyboardButton("✅ Знаю", callback_data=f"know_{word_id}")
            ],
            [
                InlineKeyboardButton("❌ Не знаю", callback_data=f"dont_know_{word_id}"),
                InlineKeyboardButton("📝 Пример", callback_data=f"example_{word_id}")
            ]
        ]
        
        if audio_enabled:
            keyboard.insert(1, [InlineKeyboardButton("🎧 Аудио-тест", callback_data=f"audiotest_{word_id}")])
        
        keyboard.append([InlineKeyboardButton("⏭ Пропустить", callback_data=f"skip_{word_id}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def after_lesson():
        keyboard = [
            [InlineKeyboardButton("📚 Еще урок", callback_data="learn_today")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def settings_menu(user):
        audio_status = "✅ Вкл" if user.audio_enabled else "❌ Выкл"
        notif_status = "✅ Вкл" if user.notification_enabled else "❌ Выкл"
        
        keyboard = [
            [InlineKeyboardButton(f"📊 Слов в день: {user.daily_words}", callback_data="change_daily")],
            [InlineKeyboardButton(f"🎯 Уровень: {user.level}", callback_data="change_level")],
            [InlineKeyboardButton(f"🔊 Аудио: {audio_status}", callback_data="toggle_audio")],
            [InlineKeyboardButton(f"🔔 Уведомления: {notif_status}", callback_data="toggle_notifications")],
            [InlineKeyboardButton(f"⏰ Время: {user.notification_time}", callback_data="change_time")],
            [InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def admin_panel_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📥 Добавить вопрос")],
        [KeyboardButton(text="📄 Посмотреть все вопросы")]
    ], resize_keyboard=True)

def user_panel_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🧠 Пройти тест")],
        [KeyboardButton(text="📚 Темы"), KeyboardButton(text="📈 Моя статистика")],
        [KeyboardButton(text="💰 Донат")]
    ], resize_keyboard=True)

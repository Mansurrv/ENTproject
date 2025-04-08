# bot.py
import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import db  # Используем глобальный объект базы данных
from handlers import admin
from handlers import user

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
    
async def main():
    await db.connect()  # Подключение к базе данных
    await db.create_tables()  # Создание таблиц, если они не существуют

    dp.include_router(admin.admin_router)
    dp.include_router(user.user_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

# admin.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from database import db  # Используем глобальный объект базы данных
from keyboards import admin_panel_kb
from keyboards import user_panel_kb
from aiogram.filters import Command

admin_router = Router()

class AddQuestion(StatesGroup):
    topic = State()
    question = State()
    option_a = State()
    option_b = State()
    option_c = State()
    option_d = State()
    correct = State()

async def is_super_admin(telegram_id):
    # Проверка, что пользователь является супер-администратором
    # Ваша логика для проверки супер-админа, например, по ID
    return telegram_id == 6040567717

# Команда для добавления администратора
@admin_router.message(Command('add_admin'))
async def add_admin(msg: Message):
    if not await is_super_admin(msg.from_user.id):
        await msg.answer("❌ У вас нет прав для добавления администраторов.")
        return

    # Получаем ID пользователя из текста команды
    text = msg.text.strip().split(maxsplit=1)
    if len(text) > 1:
        try:
            new_admin_id = int(text[1])  # ID пользователя, которого нужно добавить в администраторы
            await db.add_admin(new_admin_id)
            
            # Отправляем сообщение новому администратору
            try:
                await bot.send_message(new_admin_id, "🎉 Вы были добавлены в список администраторов бота!")
            except Exception as e:
                await msg.answer(f"❌ Не удалось отправить сообщение новому администратору. Ошибка: {e}")

            # Отправляем сообщение администратору, который добавил нового
            await msg.answer(f"✅ Пользователь с ID {new_admin_id} теперь является администратором.")

            # Перезапускаем бота
            await msg.answer("🚀 Перезапуск бота...")
            await bot.close()
            await bot.start()

        except ValueError:
            await msg.answer("❌ Пожалуйста, укажите правильный ID пользователя для добавления в администраторы.")
    else:
        await msg.answer("❌ Пожалуйста, укажите ID пользователя для добавления в администраторы.")

# Команда для удаления администратора
@admin_router.message(Command('remove_admin'))
async def remove_admin(msg: Message):
    if not await is_super_admin(msg.from_user.id):
        await msg.answer("❌ У вас нет прав для удаления администраторов.")
        return

    # Получаем ID пользователя из текста команды
    text = msg.text.strip().split(maxsplit=1)
    if len(text) > 1:
        try:
            admin_id_to_remove = int(text[1])  # ID пользователя, которого нужно удалить из администраторов
            await db.remove_admin(admin_id_to_remove)

            # Отправляем сообщение удаленному администратору
            try:
                await bot.send_message(admin_id_to_remove, "❌ Вы были удалены из списка администраторов бота.")
            except Exception as e:
                await msg.answer(f"❌ Не удалось отправить сообщение удаленному администратору. Ошибка: {e}")

            # Отправляем сообщение администратору, который удалил пользователя
            await msg.answer(f"✅ Пользователь с ID {admin_id_to_remove} больше не является администратором.")

            # Перезапускаем бота
            await msg.answer("🚀 Перезапуск бота...")
            await bot.close()
            await bot.start()

        except ValueError:
            await msg.answer("❌ Пожалуйста, укажите правильный ID пользователя для удаления из администраторов.")
    else:
        await msg.answer("❌ Пожалуйста, укажите ID пользователя для удаления из администраторов.")



# Стартовое сообщение и проверка админа
@admin_router.message(CommandStart())
async def start_handler(msg: Message):
    if await db.is_admin(msg.from_user.id):
        await msg.answer("Добро пожаловать в админ-панель!", reply_markup=admin_panel_kb())
    else:
        await msg.answer("Добро пожаловать! Выберите действие👇", reply_markup=user_panel_kb())

@admin_router.message(Command('delete'))
async def del_msg(msg: Message):
    # Проверка: админ ли пользователь
    if not await db.is_admin(msg.from_user.id):
        await msg.answer("❌ У вас нет прав для удаления вопросов.")
        return

    text = msg.text.strip().split(maxsplit=1)
    if len(text) > 1:
        command_text = text[1]  # Текст вопроса для удаления
        result = await db.delete_question(command_text)

        if result and "DELETE" in result:
            await msg.answer(f"✅ Вопрос '{command_text}' был удален из базы данных.")
        else:
            await msg.answer("❌ Не удалось найти такой вопрос для удаления.")
    else:
        await msg.answer("❌ Пожалуйста, укажите текст вопроса, который нужно удалить. Пример:\n`/delete Какой город столица Казахстана?`")


# Проверка прав администратора
async def is_admin(msg: Message):
    return await db.is_admin(msg.from_user.id)

# Обработка кнопки "📥 Добавить вопрос"
@admin_router.message(F.text == "📥 Добавить вопрос")
async def add_question_start(msg: Message, state: FSMContext):
    if await is_admin(msg):
        await msg.answer("Введите тему вопроса:")
        await state.set_state(AddQuestion.topic)
    else:
        await msg.answer("У вас нет прав для добавления вопроса.")

@admin_router.message(F.text == "📄 Посмотреть все вопросы")
async def view_all_questions(msg: Message):
    if await is_admin(msg):
        questions = await db.get_question()
        if questions:
            message = "Сұрақтар және жауабы:\n\n"
            for question in questions:
                message += f"\"{question['question']}\" - {question['correct_option']}\n"
            print(len(questions), (questions))
            await msg.answer(message)
        else:
            await msg.answer("Нет вопросов в базе данных.", reply_markup=admin_panel_kb())
    else:
        await msg.answer("У вас нет прав для просмотра вопросов.")

@admin_router.message(AddQuestion.topic)
async def get_topic(msg: Message, state: FSMContext):
    if await is_admin(msg):
        await state.update_data(topic=msg.text)
        await msg.answer("Введите сам вопрос:")
        await state.set_state(AddQuestion.question)
    else:
        await msg.answer("У вас нет прав для добавления вопроса.")

@admin_router.message(AddQuestion.question)
async def get_question(msg: Message, state: FSMContext):
    if await is_admin(msg):
        await state.update_data(question=msg.text)
        await msg.answer("Вариант A:")
        await state.set_state(AddQuestion.option_a)
    else:
        await msg.answer("У вас нет прав для добавления вопроса.")

@admin_router.message(AddQuestion.option_a)
async def get_a(msg: Message, state: FSMContext):
    if await is_admin(msg):
        await state.update_data(a=msg.text)
        await msg.answer("Вариант B:")
        await state.set_state(AddQuestion.option_b)
    else:
        await msg.answer("У вас нет прав для добавления вопроса.")

@admin_router.message(AddQuestion.option_b)
async def get_b(msg: Message, state: FSMContext):
    if await is_admin(msg):
        await state.update_data(b=msg.text)
        await msg.answer("Вариант C:")
        await state.set_state(AddQuestion.option_c)
    else:
        await msg.answer("У вас нет прав для добавления вопроса.")

@admin_router.message(AddQuestion.option_c)
async def get_c(msg: Message, state: FSMContext):
    if await is_admin(msg):
        await state.update_data(c=msg.text)
        await msg.answer("Вариант D:")
        await state.set_state(AddQuestion.option_d)
    else:
        await msg.answer("У вас нет прав для добавления вопроса.")

@admin_router.message(AddQuestion.option_d)
async def get_d(msg: Message, state: FSMContext):
    if await is_admin(msg):
        await state.update_data(d=msg.text)
        await msg.answer("Укажите правильный вариант (A/B/C/D):")
        await state.set_state(AddQuestion.correct)
    else:
        await msg.answer("У вас нет прав для добавления вопроса.")

@admin_router.message(AddQuestion.correct)
async def save_question(msg: Message, state: FSMContext):
    if await is_admin(msg):
        correct = msg.text.strip().upper()
        if correct not in ["A", "B", "C", "D"]:
            await msg.answer("Введите только A, B, C или D.")
            return
        await state.update_data(correct=correct)

        data = await state.get_data()
        await db.add_question(
            topic=data['topic'],
            question=data['question'],
            a=data['a'],
            b=data['b'],
            c=data['c'],
            d=data['d'],
            correct=correct
        )
        await msg.answer("✅ Вопрос успешно добавлен!", reply_markup=admin_panel_kb())
        await state.clear()
    else:
        await msg.answer("У вас нет прав для добавления вопроса.")




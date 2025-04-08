# user.py
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from database import db
from keyboards import user_panel_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery


user_router = Router()

# Состояния для FSM
class TestQuiz(StatesGroup):
    topic = State()
    in_progress = State()

# Команда /start для обычных пользователей
@user_router.message(CommandStart())
async def start_handler_user(msg: Message):
    if not await db.is_admin(msg.from_user.id):
        await msg.answer("Добро пожаловать в тест-бот! Выберите действие👇", reply_markup=user_panel_kb())

# Обработка кнопки "🧠 Пройти тест"
@user_router.message(F.text == "🧠 Пройти тест")
async def test_start(msg: Message, state: FSMContext):
    await state.clear() 
    topics = await db.get_topics()
    if not topics:
        await msg.answer("Темы пока не добавлены.")
        return

    buttons = [[KeyboardButton(text=topic)] for topic in topics]
    markup = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await msg.answer("Выберите тему теста:", reply_markup=markup)
    await state.set_state(TestQuiz.topic)

# Кнопка "📚 Темы" — показывает список тем
@user_router.message(F.text == "📚 Темы")
async def show_topics(msg: Message, state: FSMContext):
    await state.clear()  # сбрасываем состояние, если что-то зависло
    topics = await db.get_topics()
    if not topics:
        await msg.answer("Темы пока не добавлены.")
        return

    buttons = [[KeyboardButton(text=topic)] for topic in topics]
    markup = ReplyKeyboardMarkup(keyboard=buttons + [[KeyboardButton(text="◀️ Назад")]], resize_keyboard=True)
    await msg.answer("Выберите тему для теста:", reply_markup=markup)
    await state.set_state(TestQuiz.topic)

@user_router.message(F.text == "◀️ Назад")
async def back_to_menu(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Вы вернулись в меню.", reply_markup=user_panel_kb())

@user_router.message(F.text == "📈 Моя статистика")
async def show_stats(msg: Message):
    stats = await db.get_user_stats(msg.from_user.id)
    if stats:
        await msg.answer(
            f"📊 Ваша статистика:\n\n"
            f"🧪 Пройдено тестов: {stats['total_tests']}\n"
            f"✅ Правильных ответов: {stats['correct_answers']}"
        )
    else:
        await msg.answer("Статистика пока отсутствует. Пройдите хотя бы один тест.")

@user_router.message(F.text == "💰 Донат")
async def donate_info(msg: Message):
    await msg.answer(
        "💸 Реквизиты для доната:\n"
        "Kaspi Gold: 4400 4302 2138 9221\n"
        "Или просто отправь на Kaspi по номеру: +7 700 670 6701\n\n"
        "Если хочешь поддержать в крипте или другим способом — напиши администратору.",
        reply_markup=user_panel_kb()
    )

# Обработка выбранной темы
@user_router.message(TestQuiz.topic)
async def handle_topic(msg: Message, state: FSMContext):
    topic = msg.text
    questions = await db.get_questions_by_topic(topic)

    if not questions:
        await msg.answer("Нет вопросов по этой теме.")
        await state.clear()
        return

    await state.update_data(topic=topic, questions=questions, current=0, correct_count=0)
    await send_next_question(msg, state)

def get_answer_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="A", callback_data="answer_A"),
            InlineKeyboardButton(text="B", callback_data="answer_B")
        ],
        [
            InlineKeyboardButton(text="C", callback_data="answer_C"),
            InlineKeyboardButton(text="D", callback_data="answer_D")
        ]
    ])

async def send_next_question(msg: Message, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    current = data["current"]

    if current >= len(questions):
        score = data["correct_count"]
        total = len(questions)
        user_id = msg.from_user.id if msg.from_user else msg.chat.id
        await db.update_user_stats(user_id, score)
        await msg.answer(f"✅ Тест завершен!\nВаш результат: {score}/{total}", reply_markup=user_panel_kb())
        await state.clear()
        return

    q = questions[current]
    text = (
        f"❓ {q['question']}\n\n"
        f"A) {q['option_a']}\n"
        f"B) {q['option_b']}\n"
        f"C) {q['option_c']}\n"
        f"D) {q['option_d']}"
    )
    await msg.answer(text, reply_markup=get_answer_keyboard())
    await state.set_state(TestQuiz.in_progress)

@user_router.callback_query(TestQuiz.in_progress)
async def handle_inline_answer(callback: CallbackQuery, state: FSMContext):
    user_ans = callback.data.split("_")[1]  # "A", "B", "C" или "D"

    data = await state.get_data()
    current_q = data["questions"][data["current"]]
    correct = current_q["correct_option"]

    correct_count = 0
    if user_ans == correct:
        data["correct_count"] += 1
        correct_count = 1  # Засчитываем 1 правильный ответ

    data["current"] += 1
    await state.update_data(**data)

    # ✅ Обновляем статистику в БД сразу после ответа
    await db.update_user_stats(callback.from_user.id, correct_count)

    # Удалим сообщение с вопросом
    await callback.message.delete()

    # Следующий вопрос
    await send_next_question(callback.message, state)



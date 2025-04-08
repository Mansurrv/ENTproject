# database.py
import asyncpg
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(**DB_CONFIG)
            print("✅ База данных подключена!")
        except Exception as e:
            print(f"❌ Ошибка подключения к базе данных: {e}")
            raise

    async def create_tables(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE,
                    username TEXT
                );

                CREATE TABLE IF NOT EXISTS user_stats (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT,
                    total_tests INT DEFAULT 0,
                    correct_answers INT DEFAULT 0
                );


                CREATE TABLE IF NOT EXISTS questions (
                    id SERIAL PRIMARY KEY,
                    topic TEXT,
                    question TEXT,
                    option_a TEXT,
                    option_b TEXT,
                    option_c TEXT,
                    option_d TEXT,
                    correct_option TEXT
                );
            """)

    async def add_question(self, topic, question, a, b, c, d, correct):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO questions (topic, question, option_a, option_b, option_c, option_d, correct_option)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, topic, question, a, b, c, d, correct)

    async def is_admin(self, telegram_id):
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow("SELECT * FROM admins WHERE telegram_id = $1", telegram_id)
            return result is not None

    async def get_question(self):
        async with self.pool.acquire() as conn:
            result = await conn.fetch("""
                SELECT question,correct_option
                FROM questions
            """)
            return result

    async def delete_question(self, question_text):
        async with self.pool.acquire() as conn:
            # Удаляем вопрос по тексту
            result = await conn.execute("""
                DELETE FROM questions WHERE question = $1
            """, question_text)
            return result

    async def get_topics(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT DISTINCT topic FROM questions")
            return [row['topic'] for row in rows]

    async def get_questions_by_topic(self, topic):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT question, option_a, option_b, option_c, option_d, correct_option
                FROM questions
                WHERE topic = $1
            """, topic)
            return rows

    # Сохранение результата теста
    async def update_user_stats(self, telegram_id, correct_answers):
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM user_stats WHERE telegram_id = $1", telegram_id)
            if user:
                await conn.execute("""
                    UPDATE user_stats
                    SET total_tests = total_tests + 1,
                        correct_answers = correct_answers + $2
                    WHERE telegram_id = $1
                """, telegram_id, correct_answers)
            else:
                await conn.execute("""
                    INSERT INTO user_stats (telegram_id, total_tests, correct_answers)
                    VALUES ($1, 1, $2)
                """, telegram_id, correct_answers)

    # Получение статистики пользователя
    async def get_user_stats(self, telegram_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("""
                SELECT total_tests, correct_answers
                FROM user_stats
                WHERE telegram_id = $1
            """, telegram_id)

    # Добавление нового администратора
    async def add_admin(self, telegram_id):
        async with self.pool.acquire() as conn:
            # Проверка на существование администратора
            existing_admin = await conn.fetchrow("SELECT * FROM admins WHERE telegram_id = $1", telegram_id)
            if existing_admin:
                return "❌ Этот пользователь уже является администратором."
            
            # Добавляем пользователя как администратора
            await conn.execute("""
                INSERT INTO admins (telegram_id, username)
                VALUES ($1, $2)
            """, telegram_id, None)  # Возможно, вам нужно будет передать username или оставить None

    # Удаление администратора
    async def remove_admin(self, telegram_id):
        async with self.pool.acquire() as conn:
            # Удаляем администратора
            await conn.execute("""
                DELETE FROM admins WHERE telegram_id = $1
            """, telegram_id)



# Глобальный объект базы данных
db = Database()

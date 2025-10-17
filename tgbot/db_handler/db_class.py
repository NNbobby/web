import asyncio
import asyncpg
import uuid
from decouple import config
from datetime import datetime

# Получаем параметры для подключения к базе данных из .env файла
DATABASE_URL = config("PG_LINK")

# Создаем таблицу users, если она еще не существует
async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,       -- Новый автоинкрементный id
                added_by BIGINT NOT NULL,
                tele_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                role VARCHAR(255),
                date_reg TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                token UUID UNIQUE NOT NULL
            )
        """)
        print("Таблица 'users' успешно создана или уже существует с id! ✅")
    finally:
        await conn.close()


# Функция для добавления нового пользователя
async def add_user(added_by, tele_id, username, role, date_reg, token):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            INSERT INTO users (added_by, tele_id, username, role, date_reg, token)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, added_by, tele_id, username, role, date_reg, token)
        print(f"Пользователь {username} успешно добавлен! ✅")
    except asyncpg.UniqueViolationError:
        print(f"Ошибка: пользователь с tele_id {tele_id} уже существует! ❌")
    finally:
        await conn.close()


# Пример использования
async def main():
    await init_db()  # Инициализация базы данных
    # Пример добавления пользователя
    await add_user(
        added_by=123456789,  # ID администратора
        tele_id=987654321,   # ID нового пользователя
        username="example_user",
        role="client"        # Роль пользователя
    )

if __name__ == "__main__":
    asyncio.run(main())

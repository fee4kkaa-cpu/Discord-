import aiosqlite
import sqlite3
import os

# Устанавливаем абсолютный путь к БД в корневой папке бота
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nebula.db")

async def init_db():
    print(f"--- Инициализация БД: {DB_PATH} ---")
    async with aiosqlite.connect(DB_PATH) as db:
        
        # =================================================================
        # 1. ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ (Основная)
        # =================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                warns INTEGER DEFAULT 0,
                balance INTEGER DEFAULT 0,
                has_custom_voice INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                last_daily INTEGER DEFAULT 0,
                partner_id INTEGER DEFAULT 0,
                clan_id INTEGER DEFAULT 0,
                rep INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                deposit_time INTEGER DEFAULT 0,
                job TEXT DEFAULT 'Безработный',
                marry_time INTEGER DEFAULT 0,
                voice_time INTEGER DEFAULT 0,
                badges TEXT DEFAULT '',
                profile_color TEXT DEFAULT '#2b2d31'
            )
        """)
        
        # =================================================================
        # 2. ТАБЛИЦА НАСТРОЕК СЕРВЕРА
        # =================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS config (
                guild_id INTEGER PRIMARY KEY,
                report_channel_id INTEGER
            )
        """)

        # =================================================================
        # 3. ТАБЛИЦА КЛАНОВ
        # =================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clans (
                clan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                owner_id INTEGER,
                balance INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
        """)

        # =================================================================
        # 4. ТАБЛИЦА ИНВЕНТАРЯ
        # =================================================================
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                item_name TEXT,
                amount INTEGER DEFAULT 1,
                UNIQUE(user_id, item_name)
            )
        """)
        
        # =================================================================
        # 5. БЕЗОПАСНАЯ МИГРАЦИЯ КОЛОНОК
        # =================================================================
        # Автоматически добавит недостающие столбцы, если база была создана ранее
        columns_to_check = {
            "warns": "INTEGER DEFAULT 0",
            "balance": "INTEGER DEFAULT 0",
            "has_custom_voice": "INTEGER DEFAULT 0",
            "xp": "INTEGER DEFAULT 0",
            "level": "INTEGER DEFAULT 1",
            "last_daily": "INTEGER DEFAULT 0",
            "partner_id": "INTEGER DEFAULT 0",
            "clan_id": "INTEGER DEFAULT 0",
            "rep": "INTEGER DEFAULT 0",
            "bank": "INTEGER DEFAULT 0",
            "deposit_time": "INTEGER DEFAULT 0",
            "job": "TEXT DEFAULT 'Безработный'",
            "marry_time": "INTEGER DEFAULT 0",
            "voice_time": "INTEGER DEFAULT 0",
            "badges": "TEXT DEFAULT ''",
            "profile_color": "TEXT DEFAULT '#2b2d31'"
        }
        
        for col, col_type in columns_to_check.items():
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass # Колонка уже существует, пропускаем

        await db.commit()
    print("--- База данных успешно синхронизирована ---")

# =================================================================
# УНИВЕРСАЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ (CRUD)
# =================================================================

async def get_user(user_id: int):
    """Получает профиль пользователя, жестко фиксируя порядок колонок."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()
        
        # Вместо SELECT * перечисляем все колонки в строгом порядке, 
        # чтобы индексы (user[2] и т.д.) всегда совпадали!
        query = """
            SELECT 
                user_id, warns, balance, has_custom_voice, xp, level, 
                last_daily, partner_id, clan_id, rep, bank, deposit_time, 
                job, marry_time, voice_time, badges, profile_color 
            FROM users WHERE user_id = ?
        """
        async with db.execute(query, (user_id,)) as cursor:
            return await cursor.fetchone()

async def update_user(user_id: int, column: str, value):
    """Обновляет одну характеристику пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.execute(f"UPDATE users SET {column} = ? WHERE user_id = ?", (value, user_id))
        await db.commit()

async def add_item(user_id: int, item_name: str, amount: int = 1):
    """Добавляет предмет в инвентарь пользователя (или увеличивает его количество)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO inventory (user_id, item_name, amount) 
            VALUES (?, ?, ?) 
            ON CONFLICT(user_id, item_name) 
            DO UPDATE SET amount = amount + ?
        """, (user_id, item_name, amount, amount))
        await db.commit()

async def get_inventory(user_id: int):
    """Возвращает список предметов пользователя."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT item_name, amount FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchall()


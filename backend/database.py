import aiosqlite
import json
import os
from datetime import datetime, timedelta
from config import app_config

DB_PATH = app_config.db_path


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    db = await aiosqlite.connect(DB_PATH)
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT, avatar TEXT, city TEXT,
            age INTEGER, occupation TEXT, tags TEXT,
            taste_vector TEXT,
            privacy_level TEXT DEFAULT 'match_only'
        );
        CREATE TABLE IF NOT EXISTS meals (
            id TEXT PRIMARY KEY,
            user_id TEXT, image_url TEXT, dish_name TEXT,
            cuisine_type TEXT, ingredients TEXT,
            taste_tags TEXT, nutrition TEXT,
            meal_time TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS insights (
            id TEXT PRIMARY KEY,
            user_id TEXT, type TEXT, title TEXT, content TEXT,
            is_read INTEGER DEFAULT 0, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS matches (
            id TEXT PRIMARY KEY,
            user_a TEXT, user_b TEXT,
            similarity REAL, dim_scores TEXT,
            explanation TEXT, status TEXT DEFAULT 'pending',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS episodes (
            id TEXT PRIMARY KEY,
            user_id TEXT, type TEXT, summary TEXT,
            data TEXT, timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS auth_accounts (
            phone TEXT PRIMARY KEY,
            user_id TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            created_at TEXT,
            expires_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
    """)
    await _ensure_match_unique_index(db)
    await _ensure_session_columns(db)
    await db.commit()

    # Import mock data if tables are empty
    cursor = await db.execute("SELECT COUNT(*) FROM users")
    row = await cursor.fetchone()
    if row[0] == 0:
        await _import_mock_data(db)

    await db.close()


async def _ensure_match_unique_index(db):
    await db.execute("""
        DELETE FROM matches
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM matches
            GROUP BY user_a, user_b
        )
    """)
    await db.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_matches_user_pair ON matches(user_a, user_b)"
    )


async def _ensure_session_columns(db):
    cursor = await db.execute("PRAGMA table_info(sessions)")
    rows = await cursor.fetchall()
    columns = {row[1] for row in rows}
    if "expires_at" not in columns:
        default_expires_at = (datetime.now() + timedelta(hours=app_config.session_ttl_hours)).isoformat()
        await db.execute("ALTER TABLE sessions ADD COLUMN expires_at TEXT")
        await db.execute(
            "UPDATE sessions SET expires_at=? WHERE expires_at IS NULL OR expires_at=''",
            (default_expires_at,),
        )
    await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)")


async def _import_mock_data(db):
    data_dir = os.path.join(os.path.dirname(__file__), "data")

    # Users
    users_path = os.path.join(data_dir, "mock_users.json")
    if os.path.exists(users_path):
        with open(users_path, "r") as f:
            users = json.load(f)
        for u in users:
            await db.execute(
                "INSERT OR IGNORE INTO users (id, name, avatar, city, age, occupation, tags, taste_vector, privacy_level) VALUES (?,?,?,?,?,?,?,?,?)",
                (u["id"], u["name"], u.get("avatar", ""), u["city"], u.get("age", 25),
                 u.get("occupation", ""), json.dumps(u.get("tags", [])),
                 json.dumps(u.get("taste_vector", [])), u.get("privacy_level", "match_only"))
            )

    # Meals
    meals_path = os.path.join(data_dir, "mock_meals.json")
    if os.path.exists(meals_path):
        with open(meals_path, "r") as f:
            meals = json.load(f)
        for m in meals:
            await db.execute(
                "INSERT OR IGNORE INTO meals (id, user_id, image_url, dish_name, cuisine_type, ingredients, taste_tags, nutrition, meal_time, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (m["id"], m["user_id"], m.get("image_url", ""), m["dish_name"], m["cuisine_type"],
                 json.dumps(m.get("ingredients", [])), json.dumps(m["taste_tags"]),
                 json.dumps(m.get("nutrition", {})), m["meal_time"], m.get("created_at", m["meal_time"]))
            )

    await db.commit()

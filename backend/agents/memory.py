import json
import aiosqlite
from config import app_config
from datetime import datetime


class AgentMemory:
    """Agent 记忆系统：短期 + 长期 + 情节"""

    def __init__(self, user_id: str):
        self.user_id = user_id

    async def get_recent(self, n: int = 5) -> list[dict]:
        db = await aiosqlite.connect(app_config.db_path)
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM insights WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            (self.user_id, n)
        )
        rows = await cursor.fetchall()
        await db.close()
        return [dict(r) for r in rows]

    async def add_short_term(self, insight_type: str, title: str, content: str):
        db = await aiosqlite.connect(app_config.db_path)
        import uuid
        await db.execute(
            "INSERT INTO insights (id, user_id, type, title, content, created_at) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), self.user_id, insight_type, title, content, datetime.now().isoformat())
        )
        await db.commit()
        await db.close()

    async def add_episode(self, episode_type: str, summary: str, data: dict = None):
        db = await aiosqlite.connect(app_config.db_path)
        import uuid
        await db.execute(
            "INSERT INTO episodes (id, user_id, type, summary, data, timestamp) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), self.user_id, episode_type, summary,
             json.dumps(data or {}), datetime.now().isoformat())
        )
        await db.commit()
        await db.close()

    async def get_episodes(self, limit: int = 3) -> list[dict]:
        db = await aiosqlite.connect(app_config.db_path)
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM episodes WHERE user_id=? ORDER BY timestamp DESC LIMIT ?",
            (self.user_id, limit)
        )
        rows = await cursor.fetchall()
        await db.close()
        return [dict(r) for r in rows]

    async def get_feedback_summary(self) -> str:
        db = await aiosqlite.connect(app_config.db_path)
        cursor = await db.execute(
            "SELECT type, COUNT(*) as cnt FROM episodes WHERE user_id=? AND type='feedback' GROUP BY type",
            (self.user_id,)
        )
        rows = await cursor.fetchall()
        await db.close()
        if not rows:
            return "暂无反馈记录"
        return str(rows)

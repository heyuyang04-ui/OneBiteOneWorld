import json
import uuid
import aiosqlite
from config import app_config
from datetime import datetime

COMPRESS_RATIO_THRESHOLD = 0.5  # 上下文占用超过50%触发压缩
COMPRESS_KEEP_RECENT = 5        # 压缩后保留最新N条不动


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
        await db.execute(
            "INSERT INTO insights (id, user_id, type, title, content, created_at) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), self.user_id, insight_type, title, content, datetime.now().isoformat())
        )
        await db.commit()
        await db.close()

    async def add_episode(self, episode_type: str, summary: str, data: dict = None):
        db = await aiosqlite.connect(app_config.db_path)
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

    async def maybe_compress(self, context_ratio: float = 0.0):
        """当上下文占用超过阈值时，将旧记忆压缩成摘要"""
        if context_ratio < COMPRESS_RATIO_THRESHOLD:
            return
        from services import ai_client
        db = await aiosqlite.connect(app_config.db_path)
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, title, content, created_at FROM insights "
            "WHERE user_id=? ORDER BY created_at ASC",
            (self.user_id,)
        )
        rows = await cursor.fetchall()
        if len(rows) <= COMPRESS_KEEP_RECENT:
            await db.close()
            return
        old_rows = rows[:-COMPRESS_KEEP_RECENT]
        old_text = "\n".join(
            f"[{r['created_at'][:10]}] {r['title']}: {r['content']}" for r in old_rows
        )
        summary = await ai_client.chat(
            f"请将以下用户历史洞察记录压缩成简洁摘要（200字以内），保留关键口味特征和重要事件：\n{old_text}",
            system="你是记忆压缩助手，输出纯文本摘要。"
        )
        old_ids = [r['id'] for r in old_rows]
        placeholders = ",".join("?" * len(old_ids))
        await db.execute(f"DELETE FROM insights WHERE id IN ({placeholders})", old_ids)
        await db.execute(
            "INSERT INTO insights (id, user_id, type, title, content, created_at) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), self.user_id, "summary", "历史记忆摘要", summary,
             datetime.now().isoformat())
        )
        await db.commit()
        await db.close()
        print(f"[Memory] user={self.user_id} context_ratio={context_ratio:.1%} → compressed {len(old_rows)} records → 1 summary")

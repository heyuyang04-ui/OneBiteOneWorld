import uuid
from datetime import datetime, timedelta

import aiosqlite

from config import SESSION, app_config


def _now() -> datetime:
    return datetime.now()


def _expires_at() -> str:
    return (_now() + timedelta(hours=app_config.session_ttl_hours)).isoformat()


def _is_expired(expires_at: str) -> bool:
    if not expires_at:
        return False
    try:
        return datetime.fromisoformat(expires_at) <= _now()
    except ValueError:
        return True


def _cached_user_id(cached) -> str:
    if isinstance(cached, dict):
        return str(cached.get("user_id") or "")
    return str(cached or "")


async def create_session(user_id: str) -> str:
    session_id = str(uuid.uuid4())
    expires_at = _expires_at()
    SESSION[session_id] = {"user_id": user_id, "expires_at": expires_at}
    async with aiosqlite.connect(app_config.db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO sessions (id, user_id, created_at, expires_at) VALUES (?,?,?,?)",
            (session_id, user_id, _now().isoformat(), expires_at),
        )
        await db.commit()
    return session_id


async def resolve_session(session_id: str) -> str:
    if not session_id:
        return ""

    cached = SESSION.get(session_id)
    if isinstance(cached, dict) and _is_expired(str(cached.get("expires_at") or "")):
        await delete_session(session_id)
        return ""

    async with aiosqlite.connect(app_config.db_path) as db:
        cursor = await db.execute("SELECT user_id, expires_at FROM sessions WHERE id=?", (session_id,))
        row = await cursor.fetchone()

    if not row:
        SESSION.pop(session_id, None)
        return ""

    user_id, expires_at = row[0], row[1] or ""
    if _is_expired(expires_at):
        await delete_session(session_id)
        return ""

    SESSION[session_id] = {"user_id": user_id, "expires_at": expires_at}
    return user_id


async def delete_session(session_id: str):
    if not session_id:
        return
    SESSION.pop(session_id, None)
    async with aiosqlite.connect(app_config.db_path) as db:
        await db.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        await db.commit()


async def delete_user_sessions(user_id: str):
    if not user_id:
        return
    for session_id, cached in list(SESSION.items()):
        if _cached_user_id(cached) == user_id:
            SESSION.pop(session_id, None)
    async with aiosqlite.connect(app_config.db_path) as db:
        await db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        await db.commit()


async def cleanup_expired_sessions():
    now = _now().isoformat()
    for session_id, cached in list(SESSION.items()):
        if isinstance(cached, dict) and _is_expired(str(cached.get("expires_at") or "")):
            SESSION.pop(session_id, None)

    async with aiosqlite.connect(app_config.db_path) as db:
        await db.execute(
            "DELETE FROM sessions WHERE expires_at IS NOT NULL AND expires_at <= ?",
            (now,),
        )
        await db.commit()

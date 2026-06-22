from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json, aiosqlite, asyncio
from config import app_config
from services.session_store import resolve_session
from utils.responses import error_response

router = APIRouter()


async def _resolve_stream_user_id(request: Request) -> str:
    session_id = request.query_params.get("x_session_id", "")
    user_id = await resolve_session(session_id)
    return user_id or getattr(request.state, "user_id", "")


@router.get("")
async def get_notifications(request: Request, unread_only: bool = False):
    user_id = request.state.user_id
    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row

    query = "SELECT * FROM insights WHERE user_id=?"
    params = [user_id]
    if unread_only:
        query += " AND is_read=0"
    query += " ORDER BY created_at DESC LIMIT 20"

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    await db.close()

    notifications = [{
        "id": r["id"], "type": r["type"], "title": r["title"],
        "content": r["content"], "is_read": bool(r["is_read"]), "created_at": r["created_at"],
    } for r in rows]

    return {"success": True, "data": notifications}


@router.get("/stream")
async def notification_stream(request: Request):
    """SSE endpoint for real-time notification push"""
    user_id = await _resolve_stream_user_id(request)
    if not user_id:
        return error_response("请先登录", "UNAUTHORIZED")

    async def event_generator():
        last_count = await _get_unread_count(user_id)
        while True:
            if await request.is_disconnected():
                break
            await asyncio.sleep(5)  # Poll every 5 seconds
            if await request.is_disconnected():
                break
            try:
                current_count = await _get_unread_count(user_id)
                if current_count != last_count:
                    yield f"data: {json.dumps({'unread_count': current_count, 'delta': current_count - last_count})}\n\n"
                    last_count = current_count
                else:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
            except Exception:
                yield f": heartbeat\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def _get_unread_count(user_id: str) -> int:
    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute(
        "SELECT COUNT(*) FROM insights WHERE user_id=? AND is_read=0",
        (user_id,)
    )
    row = await cursor.fetchone()
    await db.close()
    return row[0] if row else 0


@router.post("/{notification_id}/read")
async def mark_read(notification_id: str, request: Request):
    user_id = request.state.user_id
    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute(
        "UPDATE insights SET is_read=1 WHERE id=? AND user_id=?",
        (notification_id, user_id)
    )
    await db.commit()
    changed = cursor.rowcount
    await db.close()
    if changed == 0:
        return error_response("notification not found", "NOT_FOUND")
    return {"success": True}

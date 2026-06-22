from fastapi import APIRouter, Request
from models.schemas import PrivacyRequest
import json, aiosqlite
from config import app_config
from services.session_store import create_session
from utils.responses import error_response

router = APIRouter()

DEMO_USER_IDS = {"user_01", "user_bowen", "user_02", "user_03"}


@router.get("/users")
async def list_users(request: Request):
    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row
    cursor = await db.execute("SELECT id, name, avatar, city, age, occupation, tags FROM users WHERE id IN (?,?,?,?)", tuple(DEMO_USER_IDS))
    rows = await cursor.fetchall()
    await db.close()
    users = [{"id": r["id"], "name": r["name"], "city": r["city"],
              "age": r["age"], "occupation": r["occupation"], "tags": json.loads(r["tags"])} for r in rows]
    return {"success": True, "data": users}


@router.get("/users/me")
async def get_current_user(request: Request):
    user_id = request.state.user_id
    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row
    cursor = await db.execute("SELECT * FROM users WHERE id=?", (user_id,))
    r = await cursor.fetchone()
    await db.close()

    if not r:
        return error_response("user not found", "NOT_FOUND")

    return {"success": True, "data": {
        "id": r["id"], "name": r["name"], "city": r["city"],
        "age": r["age"], "occupation": r["occupation"], "tags": json.loads(r["tags"]),
        "privacy_level": r["privacy_level"],
    }}


@router.put("/users/me/switch")
async def switch_user(request: Request, body: dict = None):
    """Switch the current demo user. Returns a session_id to be sent as X-Session-Id header."""
    if not body or "user_id" not in body:
        return error_response("user_id is required", "BAD_REQUEST")
    user_id = body["user_id"]
    if user_id not in DEMO_USER_IDS:
        return error_response("only demo users can be switched directly", "FORBIDDEN")

    # Verify user exists
    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute("SELECT id, name FROM users WHERE id=?", (user_id,))
    user = await cursor.fetchone()
    await db.close()

    if not user:
        return error_response("user not found", "NOT_FOUND")

    session_id = await create_session(user_id)
    return {"success": True, "data": {"session_id": session_id, "user_id": user_id, "user_name": user[1]}}


@router.put("/settings/privacy")
async def update_privacy(request: Request, body: PrivacyRequest):
    user_id = request.state.user_id
    db = await aiosqlite.connect(app_config.db_path)
    await db.execute("UPDATE users SET privacy_level=? WHERE id=?", (body.level, user_id))
    if body.level == "private":
        # Clear match records involving this user when going private
        await db.execute("DELETE FROM matches WHERE user_a=? OR user_b=?", (user_id, user_id))
    await db.commit()
    await db.close()
    return {"success": True}

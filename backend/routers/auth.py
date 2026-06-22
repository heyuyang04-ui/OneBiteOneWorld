import json
import re
import uuid
from datetime import datetime

import aiosqlite
from fastapi import APIRouter, Request

from config import app_config
from services.session_store import create_session, delete_session
from utils.responses import error_response

router = APIRouter()


def _normalize_phone(phone: str) -> str:
    return re.sub(r"\D", "", phone or "")


def _level_value(level: str, low: float, medium: float, high: float) -> float:
    if level == "high":
        return high
    if level == "low":
        return low
    return medium


def _infer_profile(body: dict) -> tuple[list[str], list[float]]:
    favorite = str(body.get("favorite_foods", "")).lower()
    occupation = str(body.get("occupation", ""))
    city = str(body.get("city", ""))
    spice_level = body.get("spice_level", "medium")
    sweet_level = body.get("sweet_level", "medium")
    meat_level = body.get("meat_level", "medium")
    dining_scene = body.get("dining_scene", "daily")

    vector = [0.3] * 32
    vector[0] = _level_value(spice_level, 0.18, 0.45, 0.78)
    vector[1] = _level_value(sweet_level, 0.16, 0.42, 0.72)
    vector[2] = 0.32
    vector[3] = _level_value(meat_level, 0.34, 0.56, 0.74)
    vector[4] = _level_value(meat_level, 0.38, 0.62, 0.86)
    vector[5] = 0.22

    tags: list[str] = []

    if meat_level == "high" or any(k in favorite for k in ["肉", "牛", "羊", "烤", "火锅", "steak"]):
        tags.extend(["肉食爱好者", "高蛋白偏好"])
        vector[3] = max(vector[3], 0.68)
        vector[4] = max(vector[4], 0.82)
        vector[9] = max(vector[9], 0.56)   # 鲁菜
        vector[11] = max(vector[11], 0.62) # 韩餐
        vector[12] = max(vector[12], 0.7)  # 西餐

    if spice_level == "high" or any(k in favorite for k in ["辣", "川", "湘", "麻"]):
        tags.append("重口探索型")
        vector[0] = max(vector[0], 0.76)
        vector[6] = max(vector[6], 0.72)   # 川菜
        vector[8] = max(vector[8], 0.68)   # 湘菜

    if sweet_level == "high" or any(k in favorite for k in ["甜", "蛋糕", "奶茶", "咖啡"]):
        tags.append("甜口治愈型")
        vector[1] = max(vector[1], 0.72)
        vector[7] = max(vector[7], 0.5)    # 粤菜

    if city == "beijing":
        tags.append("北京味觉探索者")
        vector[9] = max(vector[9], 0.52)
        vector[12] = max(vector[12], 0.48)

    if occupation == "程序员" or dining_scene == "work_overtime":
        tags.append("加班晚餐型")
        vector[30] = max(vector[30], 0.72) # dinner
        vector[31] = max(vector[31], 0.62) # late night
    elif dining_scene == "social":
        tags.append("社交探店型")
        vector[30] = max(vector[30], 0.64)
    elif dining_scene == "fitness":
        tags.append("控卡高蛋白型")
        vector[4] = max(vector[4], 0.68)
        vector[28] = max(vector[28], 0.58)

    if not tags:
        tags.extend(["均衡探索型", "城市味觉新用户"])

    return list(dict.fromkeys(tags))[:5], [round(min(1, max(0, v)), 2) for v in vector]


@router.post("/phone-login")
async def phone_login(body: dict):
    phone = _normalize_phone(body.get("phone", "")) if body else ""
    if not phone:
        return error_response("phone is required", "BAD_REQUEST")

    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute(
        """
        SELECT users.id, users.name
        FROM auth_accounts
        JOIN users ON users.id = auth_accounts.user_id
        WHERE auth_accounts.phone = ?
        """,
        (phone,),
    )
    user = await cursor.fetchone()
    await db.close()

    if not user:
        return error_response("phone not registered", "NOT_FOUND")

    session_id = await create_session(user[0])
    return {"success": True, "data": {"session_id": session_id, "user_id": user[0], "user_name": user[1]}}


@router.post("/register")
async def register(body: dict):
    body = body or {}
    phone = _normalize_phone(body.get("phone", ""))
    name = str(body.get("name", "")).strip()
    city = str(body.get("city", "beijing") or "beijing")
    occupation = str(body.get("occupation", "") or "")

    try:
        age = int(body.get("age", 25))
    except (TypeError, ValueError):
        age = 25
    age = max(12, min(100, age))

    if not phone or not name:
        return error_response("phone and name are required", "BAD_REQUEST")

    tags, taste_vector = _infer_profile({**body, "city": city, "occupation": occupation})
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()

    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute("SELECT user_id FROM auth_accounts WHERE phone=?", (phone,))
    existing = await cursor.fetchone()
    if existing:
        await db.close()
        return error_response("phone already registered", "CONFLICT")

    await db.execute(
        "INSERT INTO users (id, name, avatar, city, age, occupation, tags, taste_vector, privacy_level) VALUES (?,?,?,?,?,?,?,?,?)",
        (user_id, name, "", city, age, occupation, json.dumps(tags), json.dumps(taste_vector), "match_only"),
    )
    await db.execute(
        "INSERT INTO auth_accounts (phone, user_id, created_at) VALUES (?,?,?)",
        (phone, user_id, now),
    )
    await db.commit()
    await db.close()

    session_id = await create_session(user_id)
    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "user_id": user_id,
            "user_name": name,
            "tags": tags,
            "taste_vector": taste_vector,
        },
    }


@router.post("/logout")
async def logout(request: Request):
    session_id = request.headers.get("X-Session-Id", "")
    if session_id:
        await delete_session(session_id)
    return {"success": True}

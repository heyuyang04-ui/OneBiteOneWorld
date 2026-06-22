import json
import uuid
from datetime import datetime

import aiosqlite

from config import app_config
from skills.health_skill import health_skill
from skills.mood_food_skill import mood_food_skill


def _safe_tags(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        data = json.loads(raw or "{}")
    except Exception:
        data = {}
    return data if isinstance(data, dict) else {}


def _safe_nutrition(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        data = json.loads(raw or "{}")
    except Exception:
        data = {}
    return data if isinstance(data, dict) else {}


def _pick_notification(meal: dict, health: dict, mood: dict) -> dict:
    tags = _safe_tags(meal.get("taste_tags", {}))
    nutrition = _safe_nutrition(meal.get("nutrition", {}))
    calories = float(nutrition.get("calories", 0) or 0)
    dish = meal.get("dish_name") or "这餐"

    if health.get("risk_level") in {"medium", "high"} and calories >= 850:
        return {
            "type": "health",
            "title": "这餐满足感很高，下一餐建议降负担",
            "content": f"{dish} 的热量信号偏高。你可以保留喜欢的口味，但下一餐优先选汤品、蔬菜或低油蛋白。",
        }
    if mood.get("state") == "压力补偿型进食":
        return {
            "type": "mood",
            "title": "你可能在用食物对冲疲惫",
            "content": "最近的晚间或重口记录偏多。系统建议把下一餐目标设为“被照顾但不加重负担”。",
        }
    if tags.get("spicy", 0) >= 0.7 or tags.get("salty", 0) >= 0.7:
        return {
            "type": "balance",
            "title": "重口信号已记录",
            "content": f"{dish} 会强化你的重口味画像。若今天已经连续重口，下一餐可以换成清爽鲜味。",
        }
    return {
        "type": "insight",
        "title": "这餐已经加入你的味觉画像",
        "content": f"系统已记录 {dish}，会用于更新你的口味偏好、周报和餐厅匹配。",
    }


async def _exists_for_meal(user_id: str, meal_id: str) -> bool:
    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute(
        "SELECT COUNT(*) FROM insights WHERE user_id=? AND content LIKE ?",
        (user_id, f"%{meal_id}%"),
    )
    row = await cursor.fetchone()
    await db.close()
    return bool(row and row[0] > 0)


async def proactive_notify_skill(user_id: str, params: dict) -> dict:
    meal = params.get("meal", {}) if isinstance(params, dict) else {}
    meal_id = meal.get("id") or params.get("meal_id", "")
    if meal_id and await _exists_for_meal(user_id, meal_id):
        return {"saved": False, "reason": "duplicate"}

    health = await health_skill(user_id, {"limit": 30})
    mood = await mood_food_skill(user_id, {"limit": 30})
    notification = _pick_notification(meal, health, mood)
    content = notification["content"]
    if meal_id:
        content = f"{content}（记录：{meal_id}）"

    notification_id = f"insight_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()
    db = await aiosqlite.connect(app_config.db_path)
    await db.execute(
        "INSERT INTO insights (id, user_id, type, title, content, is_read, created_at) VALUES (?,?,?,?,?,?,?)",
        (notification_id, user_id, notification["type"], notification["title"], content, 0, now),
    )
    await db.commit()
    await db.close()

    return {
        "saved": True,
        "id": notification_id,
        "type": notification["type"],
        "title": notification["title"],
        "content": content,
    }

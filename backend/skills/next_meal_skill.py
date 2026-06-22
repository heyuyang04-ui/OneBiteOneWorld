import json

import aiosqlite

from config import app_config
from skills.health_skill import health_skill
from skills.mood_food_skill import mood_food_skill

TASTE_DIMS = ["spicy", "sweet", "sour", "salty", "umami", "bitter"]


def _safe_vector(raw: str) -> list[float]:
    try:
        vector = json.loads(raw or "[]")
    except Exception:
        vector = []
    if not isinstance(vector, list):
        vector = []
    return [(float(v) if isinstance(v, (int, float)) else 0.0) for v in vector]


def _taste_map(vector: list[float]) -> dict[str, float]:
    return {dim: round(vector[i], 2) if i < len(vector) else 0.0 for i, dim in enumerate(TASTE_DIMS)}


def _primary_state(taste: dict[str, float], city: str, mood: dict) -> dict:
    signals = []
    if taste["umami"] >= 0.65:
        signals.append("鲜味偏好明显")
    if taste["salty"] >= 0.6:
        signals.append("咸鲜满足感高")
    if taste["spicy"] >= 0.55:
        signals.append("能接受重口和辣味")
    if city == "beijing":
        signals.append("北京本地风味可探索")
    if mood.get("state") and mood.get("state") != "记录积累期":
        signals.append(mood["state"])

    if mood.get("state") == "压力补偿型进食":
        title = "需要被照顾的满足型"
        summary = "今天可以保留高满足感，但建议用汤品、蔬菜或低油蛋白降低负担。"
    elif taste["umami"] >= 0.65 and taste["salty"] >= 0.55:
        title = "咸鲜肉食满足型"
        summary = "今天适合高蛋白、咸鲜、满足感强的选择；如果继续吃肉，建议搭配清爽蔬菜或汤品。"
    elif taste["spicy"] >= 0.6:
        title = "重口探索型"
        summary = "今天可以选择辣味或香气更强的菜，但建议避免连续多餐过度重口。"
    else:
        title = "均衡探索型"
        summary = "今天适合在熟悉口味中加入一点新菜系，让饮食记录更有变化。"

    return {"title": title, "summary": summary, "signals": signals[:5] or ["口味状态稳定"]}


def _recommendations(taste: dict[str, float], city: str, health: dict, mood: dict) -> list[dict]:
    meat_forward = taste["umami"] >= 0.6 or taste["salty"] >= 0.6
    spicy_forward = taste["spicy"] >= 0.55
    needs_balance = health.get("risk_level") in {"medium", "high"} or mood.get("state") in {"压力补偿型进食", "高满足感偏好期"}

    if city == "beijing" and meat_forward:
        preference_items = [
            {"name": "炙子烤肉", "reason": "符合你的肉食、咸鲜和北京本地风味偏好。", "tags": ["肉食", "咸鲜", "北京"]},
            {"name": "铜锅涮肉", "reason": "保留肉类满足感，同时比烧烤更适合多人约饭。", "tags": ["高蛋白", "社交", "本地风味"]},
        ]
    elif spicy_forward:
        preference_items = [
            {"name": "川味牛肉小火锅", "reason": "匹配你的辣味接受度和高满足感需求。", "tags": ["辣", "热食", "满足感"]},
            {"name": "香辣烤鱼", "reason": "兼顾鲜味、辣味和晚餐场景。", "tags": ["辣", "鲜", "晚餐"]},
        ]
    else:
        preference_items = [
            {"name": "番茄牛腩饭", "reason": "稳定满足主食和蛋白质需求，酸甜口更容易入口。", "tags": ["均衡", "蛋白质", "下饭"]},
            {"name": "鸡汤米线", "reason": "鲜味明确，负担较轻，适合日常工作餐。", "tags": ["清爽", "鲜", "工作餐"]},
        ]

    balance_reason = "结合你的健康/情绪饮食信号，今天适合降低重口连续性。" if needs_balance else "保留满足感，同时让口味更平衡。"
    balance_items = [
        {"name": "烤鱼配蔬菜", "reason": balance_reason, "tags": ["平衡", "高蛋白", "清爽"]},
        {"name": "牛肉蔬菜汤", "reason": "延续鲜味和肉感，但降低油腻与重口疲劳。", "tags": ["低负担", "鲜味", "暖胃"]},
    ]

    explore_items = [
        {"name": "北京卤煮火烧", "reason": "适合探索北京城市风味，但建议作为尝鲜而非高频选择。", "tags": ["城市探索", "北京", "尝鲜"]},
        {"name": "韩式烤肉饭", "reason": "从肉食偏好延展到韩餐风味，适合下班后的快速满足。", "tags": ["韩餐", "肉食", "晚餐"]},
    ]

    social_items = [
        {"name": "约一个同频饭搭子", "reason": "你们可以从烤肉、火锅或烤鱼这类高共识食物开始。", "tags": ["饭搭子", "社交", "共同口味"]}
    ]

    return [
        {"type": "preference", "title": "贴合偏好", "items": preference_items},
        {"type": "balance", "title": "平衡建议", "items": balance_items},
        {"type": "explore", "title": "探索建议", "items": explore_items},
        {"type": "social", "title": "一起吃", "items": social_items},
    ]


async def next_meal_skill(user_id: str, params: dict) -> dict:
    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row
    cursor = await db.execute(
        "SELECT id, name, city, occupation, taste_vector FROM users WHERE id=?",
        (user_id,),
    )
    user = await cursor.fetchone()
    await db.close()

    if not user:
        return {"success": False, "error": {"message": "user not found"}}

    vector = _safe_vector(user["taste_vector"])
    taste = _taste_map(vector)
    city = user["city"] or ""
    health = await health_skill(user_id, {"limit": 30})
    mood = await mood_food_skill(user_id, {"limit": 30})

    return {
        "user": {"id": user["id"], "name": user["name"], "city": city, "occupation": user["occupation"]},
        "taste": taste,
        "state": _primary_state(taste, city, mood),
        "recommendations": _recommendations(taste, city, health, mood),
        "quick_actions": ["想吃肉", "想吃清淡", "想探索新店", "想找饭搭子"],
        "health_hint": health,
        "mood_hint": mood,
    }

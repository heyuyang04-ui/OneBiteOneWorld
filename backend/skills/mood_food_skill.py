import json
from collections import Counter

import aiosqlite

from config import app_config


def _safe_json(raw, fallback):
    try:
        return json.loads(raw or "")
    except Exception:
        return fallback


def _meal_hour(meal_time: str) -> int | None:
    try:
        return int((meal_time or "")[11:13])
    except (ValueError, TypeError):
        return None


def _confidence(*values: float) -> float:
    return round(max(0.35, min(0.92, sum(values) / max(1, len(values)) + 0.18)), 2)


async def mood_food_skill(user_id: str, params: dict) -> dict:
    """Infer lifestyle and emotional eating patterns from recent meals."""
    limit = int(params.get("limit", 50)) if params else 50
    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute(
        "SELECT dish_name, cuisine_type, taste_tags, nutrition, meal_time FROM meals WHERE user_id=? ORDER BY meal_time DESC LIMIT ?",
        (user_id, limit),
    )
    meals = await cursor.fetchall()
    await db.close()

    if not meals:
        return {
            "state": "记录积累期",
            "confidence": 0.35,
            "evidence": ["目前餐食记录还不够多，Agent 正在等待更多线索。"],
            "reflection": "先连续记录几餐，饮食和生活状态之间的关系会逐渐显现。",
            "question": "你希望 Agent 优先帮你观察健康、情绪，还是探索新口味？",
        }

    meal_count = len(meals)
    late_night_count = 0
    heavy_taste_count = 0
    sweet_count = 0
    high_calorie_count = 0
    cuisine_counter = Counter()
    dish_counter = Counter()

    for meal in meals:
        dish_name = meal[0] or ""
        cuisine = meal[1] or "未知"
        tags = _safe_json(meal[2], {})
        nutrition = _safe_json(meal[3], {})

        hour = _meal_hour(meal[4])
        if hour is not None and hour >= 21:
            late_night_count += 1

        heavy_score = max(tags.get("salty", 0), tags.get("umami", 0), tags.get("spicy", 0))
        if heavy_score >= 0.65:
            heavy_taste_count += 1
        if tags.get("sweet", 0) >= 0.55:
            sweet_count += 1
        if (nutrition.get("calories", 0) or 0) >= 850:
            high_calorie_count += 1

        cuisine_counter[cuisine] += 1
        if dish_name:
            dish_counter[dish_name] += 1

    late_ratio = late_night_count / meal_count
    heavy_ratio = heavy_taste_count / meal_count
    sweet_ratio = sweet_count / meal_count
    high_calorie_ratio = high_calorie_count / meal_count
    top_cuisine_ratio = cuisine_counter.most_common(1)[0][1] / meal_count if cuisine_counter else 0
    top_dish_ratio = dish_counter.most_common(1)[0][1] / meal_count if dish_counter else 0
    repeat_ratio = max(top_cuisine_ratio, top_dish_ratio)

    evidence = []

    if late_ratio >= 0.3:
        evidence.append("晚餐和夜宵记录占比偏高")
    if heavy_ratio >= 0.45:
        evidence.append("咸鲜、辣味或肉食满足感信号明显")
    if high_calorie_ratio >= 0.35:
        evidence.append("高热量餐食出现频率较高")
    if sweet_ratio >= 0.3:
        evidence.append("甜口或治愈型食物出现频率上升")
    if repeat_ratio >= 0.45 and meal_count >= 4:
        evidence.append("你在重复选择熟悉菜系或熟悉菜品")

    if late_ratio >= 0.3 and heavy_ratio >= 0.45:
        state = "压力补偿型进食"
        confidence = _confidence(late_ratio, heavy_ratio, high_calorie_ratio)
        reflection = "你最近可能不是单纯想吃重口，而是在用高满足感食物对冲疲惫或压力。"
        question = "这周哪几顿饭更像是在犒劳自己，而不是因为真的饿？"
    elif sweet_ratio >= 0.3:
        state = "甜口安慰型进食"
        confidence = _confidence(sweet_ratio, high_calorie_ratio)
        reflection = "甜口食物可能在承担一部分安慰和情绪修复的角色。"
        question = "你最近想吃甜的时候，更多是因为口味喜欢，还是因为需要一点安慰？"
    elif repeat_ratio >= 0.45 and meal_count >= 4:
        state = "安全感重复选择"
        confidence = _confidence(repeat_ratio, 0.45)
        reflection = "你最近更倾向选择熟悉的味道，这可能是在忙碌中降低决策成本。"
        question = "这些重复出现的食物，是让你安心，还是只是因为没时间选择？"
    elif heavy_ratio >= 0.5:
        state = "高满足感偏好期"
        confidence = _confidence(heavy_ratio, high_calorie_ratio)
        reflection = "近期饮食更偏向强烈风味和满足感，适合适当穿插清爽餐来避免口味疲劳。"
        question = "如果下一餐不靠重口获得满足，你会想用什么食物替代？"
    else:
        state = "稳定探索期"
        confidence = 0.52
        reflection = "你的饮食状态相对稳定，Agent 会继续观察是否出现新的口味变化。"
        question = "这周有没有哪一顿饭，让你觉得特别像现在的自己？"

    if not evidence:
        evidence = ["近期饮食信号相对平稳，没有明显异常波动。"]

    return {
        "state": state,
        "confidence": confidence,
        "evidence": evidence[:4],
        "reflection": reflection,
        "question": question,
        "metrics": {
            "late_night_ratio": round(late_ratio, 2),
            "heavy_taste_ratio": round(heavy_ratio, 2),
            "sweet_ratio": round(sweet_ratio, 2),
            "high_calorie_ratio": round(high_calorie_ratio, 2),
            "repeat_ratio": round(repeat_ratio, 2),
        },
    }

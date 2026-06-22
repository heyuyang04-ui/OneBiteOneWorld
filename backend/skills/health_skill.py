import json

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


def _risk_level(score: int) -> str:
    if score >= 80:
        return "low"
    if score >= 65:
        return "medium"
    return "high"


async def health_skill(user_id: str, params: dict) -> dict:
    """Analyze recent meals and produce lightweight health/lifestyle insight."""
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
            "health_score": 70,
            "risk_level": "unknown",
            "signals": [],
            "suggestions": ["先记录 3 餐以上，Agent 才能更准确地分析你的饮食节奏。"],
            "metrics": {
                "meal_count": 0,
                "avg_calories": 0,
                "late_night_count": 0,
                "heavy_taste_count": 0,
                "high_calorie_count": 0,
            },
        }

    total_calories = 0
    calorie_count = 0
    late_night_count = 0
    heavy_taste_count = 0
    high_calorie_count = 0
    low_protein_count = 0

    for meal in meals:
        tags = _safe_json(meal[2], {})
        nutrition = _safe_json(meal[3], {})
        calories = nutrition.get("calories", 0) or 0
        protein = nutrition.get("protein", 0) or 0

        if calories:
            total_calories += calories
            calorie_count += 1
            if calories >= 850:
                high_calorie_count += 1
        if protein and protein < 15:
            low_protein_count += 1

        hour = _meal_hour(meal[4])
        if hour is not None and hour >= 21:
            late_night_count += 1

        heavy_score = max(tags.get("salty", 0), tags.get("umami", 0), tags.get("spicy", 0))
        if heavy_score >= 0.65:
            heavy_taste_count += 1

    meal_count = len(meals)
    avg_calories = round(total_calories / calorie_count) if calorie_count else 0
    late_ratio = late_night_count / meal_count
    heavy_ratio = heavy_taste_count / meal_count
    high_calorie_ratio = high_calorie_count / meal_count

    if meal_count < 3:
        score = 70
    else:
        score = 86
        if late_ratio >= 0.3:
            score -= 10
        if avg_calories >= 850:
            score -= 10
        if heavy_ratio >= 0.5:
            score -= 8
        if high_calorie_ratio >= 0.4:
            score -= 8
        score = max(40, min(95, score))

    signals = []
    suggestions = []

    if late_ratio >= 0.3:
        signals.append({
            "type": "late_night",
            "title": "夜间进食偏多",
            "description": f"最近记录中有 {late_night_count} 餐发生在 21 点后。",
            "severity": "medium" if late_ratio < 0.5 else "high",
        })
        suggestions.append("尽量把高满足感晚餐提前，夜间如果饿可以选择汤品、酸奶或轻量蛋白。")

    if avg_calories >= 850:
        signals.append({
            "type": "high_calorie",
            "title": "单餐热量偏高",
            "description": f"近期有营养估算的餐食平均约 {avg_calories} 千卡。",
            "severity": "medium",
        })
        suggestions.append("下周可以安排 2 次低油但有蛋白质的餐食，减少连续高热量带来的负担。")

    if heavy_ratio >= 0.5:
        signals.append({
            "type": "heavy_taste",
            "title": "重口满足感偏强",
            "description": f"近期约 {round(heavy_ratio * 100)}% 的记录呈现咸鲜、辣味或高鲜味特征。",
            "severity": "medium",
        })
        suggestions.append("如果继续吃肉，优先选择烤鱼、牛肉汤、鸡肉饭，并搭配清爽蔬菜。")

    if low_protein_count >= max(2, meal_count // 3):
        signals.append({
            "type": "low_protein",
            "title": "蛋白质信号偏弱",
            "description": "部分餐食蛋白质估算偏低，可能不够抗饿。",
            "severity": "low",
        })
        suggestions.append("早餐或午餐可以增加鸡蛋、牛肉、鱼、豆制品等稳定蛋白来源。")

    if not suggestions:
        suggestions.append("本周饮食节奏相对稳定，可以继续保持记录，让 Agent 观察更长期的变化。")

    return {
        "health_score": score,
        "risk_level": _risk_level(score),
        "signals": signals,
        "suggestions": suggestions[:4],
        "metrics": {
            "meal_count": meal_count,
            "avg_calories": avg_calories,
            "late_night_count": late_night_count,
            "heavy_taste_count": heavy_taste_count,
            "high_calorie_count": high_calorie_count,
        },
    }

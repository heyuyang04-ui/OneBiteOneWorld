import json
from collections import Counter

import aiosqlite

from config import app_config


def _safe_json(raw, fallback):
    try:
        return json.loads(raw or "")
    except Exception:
        return fallback


def _hour(meal_time: str) -> int | None:
    try:
        return int((meal_time or "")[11:13])
    except Exception:
        return None


async def memory_timeline_skill(user_id: str, params: dict) -> dict:
    """Build a food autobiography timeline from recent meals."""
    limit = int(params.get("limit", 30)) if params else 30
    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute(
        "SELECT dish_name, cuisine_type, taste_tags, nutrition, meal_time FROM meals WHERE user_id=? ORDER BY meal_time DESC LIMIT ?",
        (user_id, limit),
    )
    meals = await cursor.fetchall()
    await db.close()

    if len(meals) < 3:
        return {
            "chapters": [{
                "title": "饮食自传正在开篇",
                "period": "记录积累期",
                "evidence": ["目前记录还不够多", "连续记录后会出现更清晰的生活线索"],
                "meaning": "先记录几餐，Agent 会把菜品、时间和口味变化串成你的饮食故事。",
            }]
        }

    cuisine_counter = Counter()
    dish_counter = Counter()
    late_count = 0
    meat_like_count = 0
    sweet_count = 0
    heavy_count = 0

    for meal in meals:
        dish = meal[0] or ""
        cuisine = meal[1] or "未知"
        tags = _safe_json(meal[2], {})
        hour = _hour(meal[4])
        cuisine_counter[cuisine] += 1
        if dish:
            dish_counter[dish] += 1
        if hour is not None and hour >= 21:
            late_count += 1
        if max(tags.get("umami", 0), tags.get("salty", 0)) >= 0.65:
            meat_like_count += 1
        if tags.get("sweet", 0) >= 0.55:
            sweet_count += 1
        if max(tags.get("spicy", 0), tags.get("salty", 0), tags.get("umami", 0)) >= 0.65:
            heavy_count += 1

    total = len(meals)
    chapters = []

    if late_count / total >= 0.3:
        chapters.append({
            "title": "夜晚被食物接住",
            "period": f"最近 {total} 餐",
            "evidence": [f"有 {late_count} 餐发生在 21 点后", "晚餐和夜宵成为更高频的记录场景"],
            "meaning": "这段时间的饮食更像是在忙碌后补回一点掌控感和安慰。",
        })

    if meat_like_count / total >= 0.4:
        chapters.append({
            "title": "高满足感的肉食章节",
            "period": f"最近 {total} 餐",
            "evidence": ["咸鲜/鲜味信号频繁出现", "肉食或高蛋白满足感偏强"],
            "meaning": "你正在用更直接、更有满足感的食物犒劳自己。",
        })

    if sweet_count / total >= 0.25:
        chapters.append({
            "title": "甜口安慰的片段",
            "period": f"最近 {total} 餐",
            "evidence": ["甜口信号出现频率上升", "治愈型食物更容易被选择"],
            "meaning": "甜食可能不只是口味偏好，也在承担一点情绪缓冲。",
        })

    top_cuisine, top_cuisine_count = cuisine_counter.most_common(1)[0]
    if top_cuisine_count / total >= 0.4:
        chapters.append({
            "title": f"反复回到 {top_cuisine}",
            "period": f"最近 {total} 餐",
            "evidence": [f"{top_cuisine} 是近期最高频菜系", "熟悉风味反复出现"],
            "meaning": "你可能在用熟悉的味道降低选择成本，也可能是在寻找稳定感。",
        })

    if not chapters:
        chapters.append({
            "title": "稳定探索期",
            "period": f"最近 {total} 餐",
            "evidence": ["口味没有出现明显单一高峰", "饮食选择相对分散"],
            "meaning": "你正处在比较平衡的探索状态，适合尝试一两个新风味。",
        })

    return {"chapters": chapters[:4]}

import json
from collections import Counter

import aiosqlite

from config import app_config

TASTE_DIMS = ["spicy", "sweet", "sour", "salty", "umami", "bitter"]


def _safe_json(raw, fallback):
    try:
        return json.loads(raw or "")
    except Exception:
        return fallback


async def city_aggregation_skill(user_id: str, params: dict) -> dict:
    city = params.get("city", "beijing")
    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row
    cursor = await db.execute(
        """
        SELECT meals.cuisine_type, meals.taste_tags, meals.nutrition, meals.meal_time
        FROM meals
        JOIN users ON users.id = meals.user_id
        WHERE users.city = ?
        ORDER BY meals.meal_time DESC
        LIMIT 200
        """,
        (city,),
    )
    rows = await cursor.fetchall()
    await db.close()

    if len(rows) < 3:
        return {
            "city": city,
            "source": "mock_fallback",
            "meal_count": len(rows),
            "hot_cuisines": [],
            "taste_trends": {},
            "late_night_ratio": 0,
            "heavy_taste_ratio": 0,
            "summary": "当前真实记录还不够，城市趋势暂时使用模拟数据展示。",
        }

    cuisine_counter = Counter()
    taste_sum = {dim: 0.0 for dim in TASTE_DIMS}
    late_count = 0
    heavy_count = 0

    for row in rows:
        cuisine_counter[row["cuisine_type"] or "未知"] += 1
        tags = _safe_json(row["taste_tags"], {})
        for dim in TASTE_DIMS:
            taste_sum[dim] += float(tags.get(dim, 0) or 0)
        try:
            hour = int((row["meal_time"] or "")[11:13])
            if hour >= 21:
                late_count += 1
        except Exception:
            pass
        if max(tags.get("spicy", 0), tags.get("salty", 0), tags.get("umami", 0)) >= 0.65:
            heavy_count += 1

    total = len(rows)
    return {
        "city": city,
        "source": "real",
        "meal_count": total,
        "hot_cuisines": [{"name": name, "count": count} for name, count in cuisine_counter.most_common(5)],
        "taste_trends": {dim: round(value / total, 2) for dim, value in taste_sum.items()},
        "late_night_ratio": round(late_count / total, 2),
        "heavy_taste_ratio": round(heavy_count / total, 2),
        "summary": "这是基于当前用户真实餐食记录聚合出的城市味觉信号。",
    }

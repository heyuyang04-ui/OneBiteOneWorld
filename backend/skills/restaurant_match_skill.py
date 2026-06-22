import json
import math
import os

import aiosqlite

from config import app_config

DIMS = ["spicy", "sweet", "sour", "salty", "umami", "bitter"]
CUISINE_START = 6
CUISINE_INDEX = {"川菜": 0, "粤菜": 1, "湘菜": 2, "鲁菜": 3, "日料": 4, "韩餐": 5, "西餐": 6, "东南亚": 7}


def _safe_vector(raw: str) -> list[float]:
    try:
        vector = json.loads(raw or "[]")
    except Exception:
        vector = []
    if not isinstance(vector, list):
        vector = []
    return [(float(v) if isinstance(v, (int, float)) else 0.0) for v in vector]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _load_restaurants() -> list[dict]:
    path = os.path.join(app_config.data_dir, "mock_restaurants.json")
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception:
        return []
    return data if isinstance(data, list) else []


def _preferred_cuisines(vector: list[float]) -> list[str]:
    scored = []
    for cuisine, offset in CUISINE_INDEX.items():
        idx = CUISINE_START + offset
        scored.append((cuisine, vector[idx] if idx < len(vector) else 0.0))
    scored.sort(key=lambda item: item[1], reverse=True)
    return [name for name, score in scored if score >= 0.35][:4]


def _scene_for_restaurant(rest: dict, taste: dict[str, float]) -> str:
    tags = rest.get("tags") if isinstance(rest.get("tags"), list) else []
    if "家庭" in tags:
        return "周末多人聚餐"
    if taste.get("umami", 0) >= 0.6 or taste.get("salty", 0) >= 0.6:
        return "下班后的高满足感晚餐"
    if taste.get("sweet", 0) >= 0.5:
        return "下午茶或轻松约饭"
    return "日常探店"


def _tradeoff(rest: dict, taste: dict[str, float]) -> str:
    price = rest.get("price_level", 0)
    profile = rest.get("taste_profile") if isinstance(rest.get("taste_profile"), dict) else {}
    if price >= 4:
        return "价格略高，更适合作为有目的的探店选择。"
    if abs(profile.get("spicy", 0) - taste.get("spicy", 0)) >= 0.35:
        return "辣度可能和你的偏好有差异，建议点餐时确认。"
    if profile.get("salty", 0) >= 0.75:
        return "咸鲜满足感强，但不建议连续多餐重口。"
    return "整体匹配稳定，可以作为低决策成本选择。"


def _reason(rest: dict, city_match: bool, cuisine_match: bool, taste_score: float, rating: float) -> str:
    parts = []
    if city_match:
        parts.append("与你当前城市一致")
    if cuisine_match:
        parts.append(f"菜系偏好命中{rest.get('cuisine_type', '该菜系')}")
    if taste_score >= 0.85:
        parts.append("味型曲线高度接近")
    elif taste_score >= 0.7:
        parts.append("主要味型比较接近")
    if rating >= 4.5:
        parts.append("评分表现稳定")
    return "，".join(parts) + "。" if parts else "综合口味、城市和评分后适合作为候选。"


async def restaurant_match_skill(user_id: str, params: dict) -> dict:
    city = params.get("city", "beijing")
    limit = int(params.get("limit", 6) or 6)

    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row
    cursor = await db.execute("SELECT id, name, city, taste_vector FROM users WHERE id=?", (user_id,))
    user = await cursor.fetchone()
    await db.close()

    if not user:
        return {"matches": [], "source": "mock_restaurants", "reason": "user not found"}

    vector = _safe_vector(user["taste_vector"])
    taste_values = [vector[i] if i < len(vector) else 0.0 for i in range(len(DIMS))]
    taste = {dim: taste_values[i] for i, dim in enumerate(DIMS)}
    preferred = _preferred_cuisines(vector)
    restaurants = _load_restaurants()
    scored = []

    for rest in restaurants:
        if not isinstance(rest, dict):
            continue
        profile = rest.get("taste_profile") if isinstance(rest.get("taste_profile"), dict) else {}
        rest_taste = [float(profile.get(dim, 0) or 0) for dim in DIMS]
        taste_score = _cosine(taste_values, rest_taste)
        rest_city = rest.get("city", "")
        city_match = rest_city == city or rest_city == user["city"]
        cuisine = rest.get("cuisine_type", "")
        tags = rest.get("tags") if isinstance(rest.get("tags"), list) else []
        cuisine_match = cuisine in preferred or any(tag in preferred for tag in tags)
        rating = float(rest.get("rating", 0) or 0)

        score = taste_score * 0.58
        score += (1.0 if city_match else 0.45) * 0.18
        score += (1.0 if cuisine_match else 0.25) * 0.14
        score += min(rating / 5, 1) * 0.10

        dishes = rest.get("signature_dishes") if isinstance(rest.get("signature_dishes"), list) else []
        scored.append({
            "id": rest.get("id", ""),
            "name": rest.get("name", "未知餐厅"),
            "city": rest_city,
            "district": rest.get("district", ""),
            "cuisine_type": cuisine,
            "location": rest.get("location", []),
            "price_level": rest.get("price_level", 0),
            "rating": rating,
            "tags": tags,
            "taste_profile": profile,
            "match_score": round(min(score, 1.0), 3),
            "reason": _reason(rest, city_match, cuisine_match, taste_score, rating),
            "recommended_dishes": dishes[:3],
            "best_for": _scene_for_restaurant(rest, taste),
            "tradeoff": _tradeoff(rest, taste),
        })

    scored.sort(key=lambda item: item["match_score"], reverse=True)
    return {
        "matches": scored[:limit],
        "source": "mock_restaurants",
        "preferred_cuisines": preferred,
        "taste": {dim: round(value, 2) for dim, value in taste.items()},
    }

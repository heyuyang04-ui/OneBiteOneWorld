import json
import numpy as np
import aiosqlite, os
from services import ai_client
from config import app_config
from skills.vector_skill import _cosine


async def recommend_skill(user_id: str, params: dict) -> dict:
    """个性化推荐：基于用户向量 × 餐厅/趋势匹配"""
    action = params.get("action", "restaurants")

    if action == "restaurants":
        return await _recommend_restaurants(user_id, params.get("city", "beijing"))
    elif action == "trends":
        return await _recommend_trends(user_id, params.get("city", "beijing"))
    elif action == "cross":
        return await _cross_recommend(user_id)
    return {}


async def _recommend_restaurants(user_id: str, city: str) -> dict:
    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute("SELECT taste_vector FROM users WHERE id=?", (user_id,))
    row = await cursor.fetchone()
    await db.close()

    if not row:
        return {"recommendations": []}

    user_vec = np.array(json.loads(row[0]))
    user_taste = user_vec[0:6]  # taste dims

    with open(os.path.join(app_config.data_dir, "mock_restaurants.json"), "r") as f:
        restaurants = json.load(f)

    city_restaurants = [r for r in restaurants if r.get("city") == city]
    candidates = city_restaurants if city_restaurants else restaurants

    scored = []
    for r in candidates:
        taste_prof = r["taste_profile"]
        rest_vec = np.array([taste_prof.get(d, 0) for d in ["spicy", "sweet", "sour", "salty", "umami", "bitter"]])
        score = float(_cosine(user_taste, rest_vec))
        scored.append({**r, "match_score": round(score, 3)})

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return {"recommendations": scored[:5]}


async def _recommend_trends(user_id: str, city: str = "beijing") -> dict:
    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute("SELECT taste_vector FROM users WHERE id=?", (user_id,))
    row = await cursor.fetchone()
    await db.close()

    if not row:
        return {"recommendations": []}

    with open(os.path.join(app_config.data_dir, "mock_city.json"), "r") as f:
        city_data = json.load(f)

    cities = city_data if isinstance(city_data, list) else [city_data]
    selected_cities = [c for c in cities if c.get("city") == city]
    if not selected_cities:
        selected_cities = cities[:1]

    # Find rising trends that match user preferences
    user_vec = json.loads(row[0])
    dims = ["spicy", "sweet", "sour", "salty", "umami", "bitter"]
    user_taste = {d: user_vec[i] if i < len(user_vec) else 0 for i, d in enumerate(dims)}

    rising_trends = []
    for city_item in selected_cities:
        for dist in city_item.get("districts", []):
            weeks = dist.get("weeks", [])
            if len(weeks) < 2:
                continue
            for dim in dims:
                change = weeks[-1].get("dimensions", {}).get(dim, 0) - weeks[0].get("dimensions", {}).get(dim, 0)
                if change > 0.03 and user_taste.get(dim, 0) > 0.3:
                    rising_trends.append({
                        "city": city_item.get("city", city),
                        "city_name": city_item.get("city_name", city_item.get("city", city)),
                        "district": dist.get("name", ""),
                        "dimension": dim,
                        "change": round(change, 3),
                        "your_preference": round(user_taste[dim], 2),
                    })

    return {"recommendations": rising_trends[:5]}


async def _cross_recommend(user_id: str) -> dict:
    """交叉推荐：将城市趋势与用户口味匹配，生成个性化趋势推荐"""
    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute("SELECT taste_vector FROM users WHERE id=?", (user_id,))
    row = await cursor.fetchone()
    await db.close()

    if not row:
        return {"recommendations": []}

    with open(os.path.join(app_config.data_dir, "mock_city.json"), "r") as f:
        city_data = json.load(f)

    cities = city_data if isinstance(city_data, list) else [city_data]
    user_vec = json.loads(row[0])
    dims = ["spicy", "sweet", "sour", "salty", "umami", "bitter"]
    user_taste = {d: user_vec[i] if i < len(user_vec) else 0 for i, d in enumerate(dims)}

    crossed = []
    for city in cities:
        for dist in city.get("districts", []):
            weeks = dist.get("weeks", [])
            if len(weeks) < 2:
                continue
            for dim in dims:
                change = weeks[-1].get("dimensions", {}).get(dim, 0) - weeks[0].get("dimensions", {}).get(dim, 0)
                pref = user_taste.get(dim, 0)
                if change > 0.02 and pref > 0.2:
                    # Score = user preference × trend strength
                    score = round(pref * abs(change), 4)
                    crossed.append({
                        "district": dist.get("name", ""),
                        "dimension": dim,
                        "trend_change": round(change, 3),
                        "your_preference": round(pref, 2),
                        "cross_score": score,
                        "top_cuisines": weeks[-1].get("top_cuisines", []),
                    })

    crossed.sort(key=lambda x: x["cross_score"], reverse=True)
    return {"cross_recommendations": crossed[:5]}

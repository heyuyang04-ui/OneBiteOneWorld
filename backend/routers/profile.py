from fastapi import APIRouter, Request
import json, aiosqlite
from config import app_config
from skills.vector_skill import vector_skill
from skills.memory_timeline_skill import memory_timeline_skill

router = APIRouter()

TASTE_DIMS = ["spicy", "sweet", "sour", "salty", "umami", "bitter"]
CUISINE_NAMES = ["川菜", "粤菜", "湘菜", "鲁菜", "日料", "韩餐", "西餐", "东南亚"]


@router.get("")
async def get_profile(request: Request):
    user_id = request.state.user_id
    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row

    # Get user vector
    cursor = await db.execute("SELECT taste_vector FROM users WHERE id=?", (user_id,))
    user = await cursor.fetchone()

    # Get recent meals for trend
    cursor2 = await db.execute(
        "SELECT taste_tags, cuisine_type, meal_time FROM meals WHERE user_id=? ORDER BY meal_time DESC LIMIT 50",
        (user_id,)
    )
    meals = await cursor2.fetchall()
    await db.close()

    vector = json.loads(user["taste_vector"]) if user else [0] * 32

    # Radar data from vector[0:6]
    radar_data = {TASTE_DIMS[i]: round(vector[i], 2) for i in range(6)}

    # Cuisine distribution from vector[6:14]
    cuisine_data = {CUISINE_NAMES[i]: round(vector[6 + i], 2) for i in range(8)}

    # Trends: group meals by day
    daily_trends = {}
    for m in meals:
        day = m["meal_time"][:10]
        tags = json.loads(m["taste_tags"])
        if day not in daily_trends:
            daily_trends[day] = {d: [] for d in TASTE_DIMS}
        for d in TASTE_DIMS:
            daily_trends[day][d].append(tags.get(d, 0))

    trends = []
    for day in sorted(daily_trends.keys()):
        avg = {d: round(sum(daily_trends[day][d]) / len(daily_trends[day][d]), 2) for d in TASTE_DIMS}
        trends.append({"date": day, **avg})

    # Prediction: simple trend extrapolation
    predictions = None
    if len(trends) >= 3:
        last = trends[-1]
        prev = trends[-3]
        predictions = {}
        for d in TASTE_DIMS:
            change = last[d] - prev[d]
            predictions[d] = round(min(1, max(0, last[d] + change)), 2)

    return {"success": True, "data": {
        "radar_data": radar_data,
        "cuisine_data": cuisine_data,
        "trends": trends,
        "predictions": predictions,
    }}


@router.get("/timeline")
async def get_timeline(request: Request):
    user_id = request.state.user_id
    result = await memory_timeline_skill(user_id, {"limit": 30})
    return {"success": True, "data": result}


@router.get("/vector")
async def get_vector(request: Request):
    user_id = request.state.user_id
    result = await vector_skill(user_id, {"action": "compute"})
    return {"success": True, "data": result}

from fastapi import APIRouter, Request
from skills.trend_skill import trend_skill
from skills.recommend_skill import recommend_skill
from skills.city_aggregation_skill import city_aggregation_skill
from skills.restaurant_match_skill import restaurant_match_skill
import json, os, time
from config import app_config

router = APIRouter()
TRENDS_CACHE_TTL = 300
_trends_cache = {}


@router.get("/live-summary")
async def get_live_summary(request: Request, city: str = "beijing"):
    result = await city_aggregation_skill(request.state.user_id, {"city": city})
    return {"success": True, "data": result}


@router.get("/heatmap")
async def get_heatmap(request: Request, dimension: str = "spicy", city: str = "beijing", week: int = -1):
    # Filter by city
    with open(os.path.join(app_config.data_dir, "mock_city.json"), "r") as f:
        all_cities = json.load(f)

    city_data = next((c for c in all_cities if c["city"] == city), all_cities[0] if all_cities else None)
    if not city_data:
        return {"success": True, "data": {"regions": []}}

    week_idx = week if week >= 0 else -1
    regions = []
    for dist in city_data["districts"]:
        w = dist["weeks"][week_idx] if dist["weeks"] else {}
        regions.append({
            "id": dist["id"],
            "name": dist["name"],
            "center": dist["center"],
            "value": w.get("dimensions", {}).get(dimension, 0),
            "top_cuisines": w.get("top_cuisines", []),
            "meal_count": w.get("meal_count", 0),
        })

    return {"success": True, "data": {"city": city, "city_name": city_data.get("city_name", city), "dimension": dimension, "regions": regions}}


@router.get("/trends")
async def get_trends(request: Request, dimension: str = "spicy", city: str = "beijing"):
    cache_key = (city, dimension)
    cached = _trends_cache.get(cache_key)
    now = time.time()
    if cached and now - cached["time"] < TRENDS_CACHE_TTL:
        return {"success": True, "data": cached["data"]}

    with open(os.path.join(app_config.data_dir, "mock_city.json"), "r") as f:
        all_cities = json.load(f)

    city_data = next((c for c in all_cities if c["city"] == city), None)
    if not city_data:
        return {"success": True, "data": {"trends": []}}

    trends = []
    for dist in city_data["districts"]:
        values = [w["dimensions"].get(dimension, 0) for w in dist["weeks"]]
        weeks = [w["week"] for w in dist["weeks"]]
        change = values[-1] - values[0] if len(values) >= 2 else 0
        trends.append({"district": dist["name"], "values": values, "weeks": weeks, "change": round(change, 3)})

    # Get AI insight for the same city context
    insight_result = await trend_skill(request.state.user_id, {"action": "insight", "city": city})
    data = {"city": city, "city_name": city_data.get("city_name", city), "dimension": dimension, "trends": trends, "insights": insight_result.get("insights", [])}
    _trends_cache[cache_key] = {"time": now, "data": data}
    return {"success": True, "data": data}


@router.get("/recommend")
async def get_recommend(request: Request, city: str = "beijing"):
    user_id = request.state.user_id
    restaurants = await recommend_skill(user_id, {"action": "restaurants", "city": city})
    matched = await restaurant_match_skill(user_id, {"city": city, "limit": 6})
    trends = await recommend_skill(user_id, {"action": "trends", "city": city})
    cross = await recommend_skill(user_id, {"action": "cross"})
    return {"success": True, "data": {
        "restaurants": restaurants.get("recommendations", []),
        "matched_restaurants": matched.get("matches", []),
        "restaurant_match_meta": {
            "source": matched.get("source", ""),
            "preferred_cuisines": matched.get("preferred_cuisines", []),
            "taste": matched.get("taste", {}),
        },
        "trends": trends.get("recommendations", []),
        "cross": cross.get("cross_recommendations", []),
    }}


@router.get("/district/{district_id}")
async def get_district(district_id: str, request: Request):
    with open(os.path.join(app_config.data_dir, "mock_city.json"), "r") as f:
        all_cities = json.load(f)
    with open(os.path.join(app_config.data_dir, "mock_restaurants.json"), "r") as f:
        all_restaurants = json.load(f)

    # Find district
    dist_info = None
    city_info = None
    for city_item in all_cities:
        for d in city_item["districts"]:
            if d["id"] == district_id:
                dist_info = d
                city_info = city_item
                break
        if dist_info:
            break

    if not dist_info:
        return {"success": False, "error": {"message": "district not found"}}

    # Get restaurants in district
    district_restaurants = [r for r in all_restaurants if r.get("district") == district_id][:10]

    # Latest week data
    latest_week = dist_info["weeks"][-1] if dist_info["weeks"] else {}

    return {"success": True, "data": {
        "city": city_info.get("city", "") if city_info else "",
        "city_name": city_info.get("city_name", "") if city_info else "",
        "district": {"id": dist_info["id"], "name": dist_info["name"], "center": dist_info["center"]},
        "taste_profile": latest_week.get("dimensions", {}),
        "top_cuisines": latest_week.get("top_cuisines", []),
        "meal_count": latest_week.get("meal_count", 0),
        "restaurants": district_restaurants,
    }}


@router.get("/cities")
async def list_cities():
    with open(os.path.join(app_config.data_dir, "mock_city.json"), "r") as f:
        all_cities = json.load(f)
    cities = [{"id": c["city"], "name": c.get("city_name", c["city"]), "districts": len(c["districts"])} for c in all_cities]
    return {"success": True, "data": cities}

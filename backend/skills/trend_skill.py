import json, os
from services import ai_client
from config import app_config


def _select_city(city_data, city_id: str):
    cities = city_data if isinstance(city_data, list) else [city_data]
    return next((item for item in cities if item.get("city") == city_id), cities[0] if cities else {"districts": []})


async def trend_skill(user_id: str, params: dict) -> dict:
    """城市趋势分析"""
    action = params.get("action", "heatmap")
    city_id = params.get("city", "beijing")

    with open(os.path.join(app_config.data_dir, "mock_city.json"), "r") as f:
        all_city_data = json.load(f)

    city_data = _select_city(all_city_data, city_id)

    if action == "heatmap":
        dimension = params.get("dimension", "spicy")
        week_idx = params.get("week", -1)  # -1 = latest
        regions = []
        for dist in city_data.get("districts", []):
            weeks = dist.get("weeks", [])
            if not weeks:
                continue
            week_data = weeks[week_idx]
            regions.append({
                "id": dist.get("id", ""),
                "name": dist.get("name", ""),
                "center": dist.get("center", []),
                "value": week_data.get("dimensions", {}).get(dimension, 0),
                "top_cuisines": week_data.get("top_cuisines", []),
                "meal_count": week_data.get("meal_count", 0),
            })
        return {"city": city_id, "dimension": dimension, "regions": regions}

    elif action == "trends":
        dimension = params.get("dimension", "spicy")
        trends = []
        for dist in city_data.get("districts", []):
            weeks = dist.get("weeks", [])
            values = [w.get("dimensions", {}).get(dimension, 0) for w in weeks]
            change = values[-1] - values[0] if len(values) >= 2 else 0
            trends.append({
                "district": dist.get("name", ""),
                "values": values,
                "weeks": [w.get("week", "") for w in weeks],
                "change": round(change, 3),
            })
        return {"city": city_id, "dimension": dimension, "trends": trends}

    elif action == "insight":
        trends_data = []
        for dist in city_data.get("districts", []):
            for dim in ["spicy", "sweet", "sour", "salty"]:
                weeks = dist.get("weeks", [])
                values = [w.get("dimensions", {}).get(dim, 0) for w in weeks]
                if len(values) < 2:
                    continue
                change = values[-1] - values[0]
                if abs(change) > 0.05:
                    trends_data.append(f"{dist.get('name', '')}的{dim}指数4周变化:{round(change,2)}")

        if not trends_data:
            return {"insights": []}

        prompt = f"""基于城市饮食趋势数据，生成2-3条简短洞察：
{chr(10).join(trends_data)}
返回JSON（不要代码块）：
{{"insights": [{{"title": "标题", "content": "内容"}}]}}"""

        raw = await ai_client.chat(prompt)
        try:
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(text)
        except Exception:
            return {"insights": []}

    return {}

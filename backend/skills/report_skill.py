import hashlib
import json
import aiosqlite
from services import ai_client
from config import app_config
from skills.health_skill import health_skill
from skills.mood_food_skill import mood_food_skill


def _safe_json(raw, fallback):
    try:
        return json.loads(raw or "")
    except Exception:
        return fallback


def _with_highlight_ids(user_id: str, highlights: list) -> list:
    result = []
    for index, item in enumerate(highlights or []):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", ""))
        digest = hashlib.sha1(f"{user_id}:{index}:{title}".encode("utf-8")).hexdigest()[:10]
        result.append({**item, "id": item.get("id") or f"weekly_{index}_{digest}"})
    return result


async def report_skill(user_id: str, params: dict) -> dict:
    """调用 LLM 生成味觉周报，并附加健康/生活状态洞察。"""
    health_insight = await health_skill(user_id, {"limit": 50})
    mood_insight = await mood_food_skill(user_id, {"limit": 50})

    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute(
        "SELECT dish_name, cuisine_type, taste_tags, nutrition, meal_time FROM meals WHERE user_id=? ORDER BY created_at DESC LIMIT 21",
        (user_id,)
    )
    meals = await cursor.fetchall()
    await db.close()

    if not meals:
        return {
            "summary": "本周暂无用餐记录。先记录几餐，Agent 会开始为你观察饮食节奏和生活状态。",
            "highlights": [],
            "reflection": mood_insight.get("question", "你希望 Agent 优先帮你观察哪类饮食变化？"),
            "data_summary": {"meal_count": 0},
            "health_insight": health_insight,
            "mood_insight": mood_insight,
        }

    cuisines = {}
    total_cal = 0
    taste_sums = {"spicy": 0, "sweet": 0, "sour": 0, "salty": 0, "umami": 0, "bitter": 0}
    late_night_count = 0

    for m in meals:
        cuisine = m[1]
        cuisines[cuisine] = cuisines.get(cuisine, 0) + 1
        tags = _safe_json(m[2], {})
        nutrition = _safe_json(m[3], {})
        total_cal += nutrition.get("calories", 0) or 0
        for k in taste_sums:
            taste_sums[k] += tags.get(k, 0)
        try:
            hour = int(m[4][11:13])
            if hour >= 21:
                late_night_count += 1
        except (ValueError, IndexError, TypeError):
            pass

    n = len(meals)
    data_summary = {
        "meal_count": n,
        "avg_calories": round(total_cal / n) if n else 0,
        "top_cuisines": sorted(cuisines.items(), key=lambda x: -x[1])[:3],
        "taste_avg": {k: round(v / n, 2) for k, v in taste_sums.items()},
        "late_night_meals": late_night_count,
    }

    prompt = f"""你是一个温暖有洞察力的味觉分析师。基于用户一周饮食数据生成简短味觉周报。

本周数据：{json.dumps(data_summary, ensure_ascii=False)}
健康/生活方式信号：{json.dumps(health_insight, ensure_ascii=False)}
情绪饮食/生活状态信号：{json.dumps(mood_insight, ensure_ascii=False)}

要求：
- 2-3个关键洞察（发现有趣模式）
- 口味变化趋势分析
- 如果存在夜间进食、重口补偿、甜口安慰、重复选择等信号，要温柔提及
- 不要使用医疗诊断语气，不要制造焦虑
- 语气像了解用户的朋友
- 生成一个反思问题（reflection），引导用户思考自己的饮食与生活状态之间的关系
- 返回JSON（不要markdown代码块）：
{{"summary": "一句话总结", "highlights": [{{"title": "洞察标题", "content": "详细内容"}}], "reflection": "一个引导用户自我反思的问题"}}"""

    raw = await ai_client.chat(prompt)
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed = json.loads(text)
    except Exception:
        parsed = {"summary": raw[:100], "highlights": [], "reflection": mood_insight.get("question", "这周的饮食，符合你想成为的样子吗？")}

    return {
        "summary": parsed.get("summary", ""),
        "highlights": _with_highlight_ids(user_id, parsed.get("highlights", [])),
        "reflection": parsed.get("reflection", ""),
        "data_summary": data_summary,
        "health_insight": health_insight,
        "mood_insight": mood_insight,
    }

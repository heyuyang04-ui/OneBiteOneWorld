import json
import aiosqlite, os
from services import ai_client
from config import app_config
from skills.vector_skill import _cosine
import numpy as np


def _bounded_limit(value, default: int = 20) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = default
    return max(1, min(limit, 50))


def _is_internal_test_user(user_id: str, name: str) -> bool:
    text = f"{user_id} {name}".lower()
    blocked_keywords = ["测试", "冒烟", "test", "smoke", "validation"]
    return any(keyword in text for keyword in blocked_keywords)


def _safe_json_loads(value, default):
    try:
        return json.loads(value) if value else default
    except (TypeError, json.JSONDecodeError):
        return default


async def match_skill(user_id: str, params: dict) -> dict:
    """匹配计算 + LLM 生成匹配解释"""
    action = params.get("action", "discover")

    if action == "discover":
        return await _discover_matches(user_id, _bounded_limit(params.get("limit", 20)))
    elif action == "explain":
        return await _explain_match(user_id, params.get("other_user_id", ""))
    elif action == "joint_recommend":
        return await _joint_recommend(user_id, params.get("other_user_id", ""))
    return {}


async def _discover_matches(user_id: str, limit: int = 20) -> dict:
    limit = _bounded_limit(limit)
    db = await aiosqlite.connect(app_config.db_path)
    cursor_me = await db.execute("SELECT taste_vector FROM users WHERE id=?", (user_id,))
    me = await cursor_me.fetchone()
    cursor_others = await db.execute(
        "SELECT id, name, city, age, occupation, tags, taste_vector, privacy_level FROM users WHERE id!=?",
        (user_id,)
    )
    others = await cursor_others.fetchall()
    await db.close()

    if not me:
        return {"matches": []}

    vec_me_data = _safe_json_loads(me[0], [])
    if len(vec_me_data) < 32:
        return {"matches": []}

    vec_me = np.array(vec_me_data)
    results = []

    for other in others:
        if other[7] == "private" or _is_internal_test_user(other[0], other[1]):
            continue

        vec_other_data = _safe_json_loads(other[6], [])
        if len(vec_other_data) < 32:
            continue

        vec_other = np.array(vec_other_data)
        score = float(_cosine(vec_me, vec_other))

        # Dimension scores
        dim_scores = {
            "taste": float(_cosine(vec_me[0:6], vec_other[0:6])),
            "cuisine": float(_cosine(vec_me[6:14], vec_other[6:14])),
            "temporal": float(_cosine(vec_me[28:32], vec_other[28:32])),
        }

        # Find common and different tastes
        tags_me = {k: vec_me[i] for i, k in enumerate(["spicy", "sweet", "sour", "salty", "umami", "bitter"])}
        tags_other = {k: vec_other[i] for i, k in enumerate(["spicy", "sweet", "sour", "salty", "umami", "bitter"])}
        common = [k for k in tags_me if tags_me[k] > 0.3 and tags_other[k] > 0.3]
        diff = [k for k in tags_me if abs(tags_me[k] - tags_other[k]) > 0.4]
        tags = _safe_json_loads(other[5], [])

        results.append({
            "user": {"id": other[0], "name": other[1], "city": other[2],
                     "age": other[3], "occupation": other[4], "tags": tags},
            "score": round(score, 3),
            "dim_scores": {k: round(v, 3) for k, v in dim_scores.items()},
            "common": common,
            "diff": diff,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return {"matches": results[:limit]}


async def _explain_match(user_id: str, other_id: str) -> dict:
    db = await aiosqlite.connect(app_config.db_path)
    cursor_a = await db.execute("SELECT name, taste_vector, tags FROM users WHERE id=?", (user_id,))
    cursor_b = await db.execute("SELECT name, taste_vector, tags FROM users WHERE id=?", (other_id,))
    a = await cursor_a.fetchone()
    b = await cursor_b.fetchone()
    await db.close()

    if not a or not b:
        return {"explanation": ""}

    prompt = f"""两个用户的味觉匹配解释：
用户A "{a[0]}" 标签:{a[2]} 向量前6维(口味):{json.loads(a[1])[:6]}
用户B "{b[0]}" 标签:{b[2]} 向量前6维(口味):{json.loads(b[1])[:6]}

用2-3句话解释为什么他们是味觉伴侣，要有趣，不要太正式。直接返回文本。"""

    explanation = await ai_client.chat(prompt)
    return {"explanation": explanation}


async def _joint_recommend(user_id: str, other_id: str) -> dict:
    db = await aiosqlite.connect(app_config.db_path)
    cursor_a = await db.execute("SELECT name, taste_vector FROM users WHERE id=?", (user_id,))
    cursor_b = await db.execute("SELECT name, taste_vector FROM users WHERE id=?", (other_id,))
    a = await cursor_a.fetchone()
    b = await cursor_b.fetchone()

    # Load restaurants
    cursor_r = await db.execute("SELECT * FROM users LIMIT 0")  # just for schema
    await db.close()

    with open(os.path.join(app_config.data_dir, "mock_restaurants.json"), "r") as f:
        restaurants = json.load(f)

    prompt = f"""两个用户想一起吃饭：
用户A "{a[0]}" 口味偏好:{json.loads(a[1])[:6]}
用户B "{b[0]}" 口味偏好:{json.loads(b[1])[:6]}
可选餐厅：{json.dumps([r['name']+'('+r['cuisine_type']+')' for r in restaurants[:10]], ensure_ascii=False)}

请以两个Agent对话形式推荐2-3家餐厅：
返回JSON（不要代码块）：
{{"dialogue": [{{"agent": "A", "content": "..."}}, {{"agent": "B", "content": "..."}}], "recommendations": [{{"restaurant": "名字", "reason": "原因"}}]}}"""

    raw = await ai_client.chat(prompt)
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)
    except Exception:
        return {"dialogue": [], "recommendations": []}

import json
import numpy as np
import aiosqlite
from config import app_config

TASTE_DIMS = ["spicy", "sweet", "sour", "salty", "umami", "bitter"]
CUISINE_MAP = {"川菜": 0, "粤菜": 1, "湘菜": 2, "鲁菜": 3, "日料": 4, "韩餐": 5, "西餐": 6, "东南亚": 7}


async def vector_skill(user_id: str, params: dict) -> dict:
    """计算/更新用户味觉向量，或计算两用户相似度"""
    action = params.get("action", "compute")

    if action == "compute":
        return await _compute_vector(user_id)
    elif action == "similarity":
        other_id = params.get("other_user_id", "")
        return await _compute_similarity(user_id, other_id)
    elif action == "batch_similarity":
        return await _batch_similarity(user_id)
    return {}


async def _compute_vector(user_id: str) -> dict:
    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute(
        "SELECT taste_tags, cuisine_type, meal_time FROM meals WHERE user_id=? ORDER BY created_at DESC LIMIT 50",
        (user_id,)
    )
    rows = await cursor.fetchall()
    if not rows:
        vector_list = [0.0] * 32
        await db.execute("UPDATE users SET taste_vector=? WHERE id=?", (json.dumps(vector_list), user_id))
        await db.commit()
        await db.close()
        return {"vector": vector_list}

    vector = np.zeros(32)
    for row in rows:
        tags = json.loads(row[0])
        cuisine = row[1]
        meal_time = row[2]

        # [0:6] taste preferences
        for i, dim in enumerate(TASTE_DIMS):
            vector[i] += tags.get(dim, 0)
        # [6:14] cuisine preferences
        if cuisine in CUISINE_MAP:
            vector[6 + CUISINE_MAP[cuisine]] += 1
        # [28:32] temporal features (simplified)
        try:
            hour = int(meal_time[11:13]) if len(meal_time) > 13 else 12
            if hour < 10:
                vector[28] += 1  # breakfast
            elif hour < 15:
                vector[29] += 1  # lunch
            elif hour < 20:
                vector[30] += 1  # dinner
            else:
                vector[31] += 1  # late night
        except (ValueError, IndexError):
            vector[29] += 1

    # Normalize
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm

    vector_list = vector.tolist()

    # Update user record
    await db.execute("UPDATE users SET taste_vector=? WHERE id=?", (json.dumps(vector_list), user_id))
    await db.commit()
    await db.close()
    return {"vector": vector_list}


async def _compute_similarity(user_a: str, user_b: str) -> dict:
    db = await aiosqlite.connect(app_config.db_path)
    cursor_a = await db.execute("SELECT taste_vector FROM users WHERE id=?", (user_a,))
    cursor_b = await db.execute("SELECT taste_vector FROM users WHERE id=?", (user_b,))
    row_a = await cursor_a.fetchone()
    row_b = await cursor_b.fetchone()
    await db.close()

    if not row_a or not row_b:
        return {"similarity": 0, "dim_scores": {}}

    vec_a = np.array(json.loads(row_a[0]))
    vec_b = np.array(json.loads(row_b[0]))

    # Weighted cosine similarity by dimension groups
    weights = {"taste": 0.30, "cuisine": 0.25, "temporal": 0.15}
    dim_scores = {}

    # Taste similarity [0:6]
    dim_scores["taste"] = float(_cosine(vec_a[0:6], vec_b[0:6]))
    # Cuisine similarity [6:14]
    dim_scores["cuisine"] = float(_cosine(vec_a[6:14], vec_b[6:14]))
    # Temporal [28:32]
    dim_scores["temporal"] = float(_cosine(vec_a[28:32], vec_b[28:32]))

    overall = (dim_scores["taste"] * 0.30 + dim_scores["cuisine"] * 0.25 +
               dim_scores["temporal"] * 0.15 + 0.30 * float(_cosine(vec_a, vec_b)))

    return {"similarity": round(overall, 3), "dim_scores": {k: round(v, 3) for k, v in dim_scores.items()}}


async def _batch_similarity(user_id: str) -> dict:
    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute("SELECT id, taste_vector, privacy_level FROM users WHERE id!=?", (user_id,))
    others = await cursor.fetchall()
    cursor_me = await db.execute("SELECT taste_vector FROM users WHERE id=?", (user_id,))
    me = await cursor_me.fetchone()
    await db.close()

    if not me:
        return {"matches": []}

    vec_me = np.array(json.loads(me[0]))
    results = []

    for other in others:
        if other[2] == "private":
            continue
        vec_other = np.array(json.loads(other[1]))
        score = float(_cosine(vec_me, vec_other))
        results.append({"user_id": other[0], "score": round(score, 3)})

    results.sort(key=lambda x: x["score"], reverse=True)
    return {"matches": results[:10]}


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

from fastapi import APIRouter, Request
from models.schemas import MatchActionRequest
from skills.match_skill import match_skill
from skills.meal_companion_skill import meal_companion_skill
import json, uuid, aiosqlite
from datetime import datetime
from config import app_config

router = APIRouter()


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


def _build_match_explanation(match: dict) -> str:
    common = match.get("common", [])
    taste_text = "、".join(common[:3]) if common else "基础口味"
    score = round(match.get("score", 0) * 100)
    return f"你们在{taste_text}上有相似信号，综合匹配度约 {score}%，适合从低压力约饭开始。"


def _dim_text(dims: list[str]) -> str:
    labels = {"spicy": "辣味", "sweet": "甜口", "sour": "酸爽", "salty": "咸香", "umami": "鲜味", "bitter": "复杂风味"}
    return "、".join([labels.get(dim, dim) for dim in dims[:3]])


def _build_match_agent_advice(match: dict) -> dict:
    common = match.get("common", [])
    diff = match.get("diff", [])
    score = round(match.get("score", 0) * 100)
    user_tags = match.get("user", {}).get("tags", []) or []
    common_text = _dim_text(common) if common else "饮食节奏和城市味觉信号"
    diff_text = _dim_text(diff) if diff else "探索边界"

    why = f"Agent 看到你们在{common_text}上有共同偏好，匹配度约 {score}%。"
    if diff:
        why += f" 同时 TA 在{diff_text}上和你略有差异，适合帮你打开新的点餐选择。"
    else:
        why += " 你们的口味路径比较接近，第一次约饭决策成本较低。"
    if user_tags:
        why += f" TA 的标签里有“{user_tags[0]}”，可以作为第一句聊天切入点。"

    if any(dim in common for dim in ["spicy", "salty", "umami"]):
        first_meal = "第一次可以选川湘小馆、烤鱼、烧烤或热汤面，点几道可分享的小份菜更容易交流。"
    elif any(dim in common for dim in ["sweet", "sour"]):
        first_meal = "第一次可以从甜品咖啡、酸甜口轻餐或融合菜开始，氛围轻松且不容易踩雷。"
    else:
        first_meal = "第一次建议选择菜品覆盖面更宽的家常菜、融合菜或商场餐厅，让双方都有安全选择。"

    starter = "可以问 TA：最近有没有吃到一道看起来普通、但吃完很上头的菜？"
    if user_tags:
        starter = f"可以从“{user_tags[0]}”聊起，再问 TA 最近最想复吃的一家店。"

    return {
        "why_recommended": why,
        "first_meal_suggestion": first_meal,
        "conversation_starter": starter,
    }


@router.get("/discover")
async def discover_matches(request: Request, limit: int = 20):
    user_id = request.state.user_id
    bounded_limit = _bounded_limit(limit)
    result = await match_skill(user_id, {"action": "discover", "limit": bounded_limit})
    matches = result.get("matches", [])

    for m in matches[:6]:
        m["explanation"] = _build_match_explanation(m)
        m.update(_build_match_agent_advice(m))

    return {"success": True, "data": matches}


@router.post("/{other_user_id}/action")
async def match_action(other_user_id: str, request: Request, body: MatchActionRequest):
    user_id = request.state.user_id
    db = await aiosqlite.connect(app_config.db_path)

    if body.action == "like":
        user_cursor = await db.execute("SELECT privacy_level FROM users WHERE id=?", (other_user_id,))
        other_user = await user_cursor.fetchone()
        if not other_user:
            await db.close()
            return {"success": False, "error": {"message": "user not found"}}
        if other_user[0] == "private":
            await db.close()
            return {"success": False, "error": {"message": "该用户已关闭匹配"}}

        from skills.vector_skill import vector_skill
        sim_result = await vector_skill(user_id, {"action": "similarity", "other_user_id": other_user_id})

        try:
            await db.execute("BEGIN IMMEDIATE")
            own_cursor = await db.execute(
                "SELECT status FROM matches WHERE user_a=? AND user_b=? AND status IN ('pending','mutual') ORDER BY created_at DESC LIMIT 1",
                (user_id, other_user_id)
            )
            own_existing = await own_cursor.fetchone()
            if own_existing:
                await db.commit()
                await db.close()
                status = own_existing[0]
                return {"success": True, "data": {"status": status, "mutual": status == "mutual", "existing": True}}

            cursor = await db.execute(
                "SELECT * FROM matches WHERE user_a=? AND user_b=? AND status='pending'",
                (other_user_id, user_id)
            )
            existing = await cursor.fetchone()

            if existing:
                await db.execute(
                    "UPDATE matches SET status='mutual' WHERE user_a=? AND user_b=?",
                    (other_user_id, user_id)
                )
                await db.commit()
                await db.close()
                return {"success": True, "data": {"status": "mutual", "mutual": True}}

            await db.execute(
                "INSERT OR IGNORE INTO matches (id, user_a, user_b, similarity, dim_scores, status, created_at) VALUES (?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), user_id, other_user_id,
                 sim_result.get("similarity", 0),
                 json.dumps(sim_result.get("dim_scores", {})),
                 "pending", datetime.now().isoformat())
            )
            await db.commit()
            await db.close()
            return {"success": True, "data": {"status": "pending", "mutual": False}}
        except Exception:
            await db.rollback()
            await db.close()
            raise
    else:
        await db.close()
        return {"success": True, "data": {"status": "skipped"}}


@router.get("/list")
async def match_list(request: Request, status: str = "mutual"):
    user_id = request.state.user_id
    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row

    cursor = await db.execute(
        "SELECT * FROM matches WHERE (user_a=? OR user_b=?) AND status=?",
        (user_id, user_id, status)
    )
    rows = await cursor.fetchall()

    matches = []
    for r in rows:
        other_id = r["user_b"] if r["user_a"] == user_id else r["user_a"]
        u_cursor = await db.execute("SELECT id, name, city, age, occupation, tags FROM users WHERE id=?", (other_id,))
        u = await u_cursor.fetchone()
        if u and not _is_internal_test_user(u["id"], u["name"]):
            matches.append({
                "match_id": r["id"],
                "user": {"id": u["id"], "name": u["name"], "city": u["city"],
                         "age": u["age"], "occupation": u["occupation"], "tags": json.loads(u["tags"])},
                "status": r["status"],
                "direction": "outgoing" if r["user_a"] == user_id else "incoming",
                "created_at": r["created_at"],
            })
    await db.close()
    return {"success": True, "data": matches}


@router.get("/{match_id}/detail")
async def match_detail(match_id: str, request: Request):
    user_id = request.state.user_id

    # Get the other user's ID from match_id (treat as other_user_id directly for demo)
    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row
    cursor = await db.execute("SELECT * FROM matches WHERE id=?", (match_id,))
    match_row = await cursor.fetchone()

    if not match_row:
        await db.close()
        return {"success": False, "error": {"message": "match not found"}}
    if match_row["user_a"] != user_id and match_row["user_b"] != user_id:
        await db.close()
        return {"success": False, "error": {"message": "not authorized"}}

    other_id = match_row["user_b"] if match_row["user_a"] == user_id else match_row["user_a"]

    # Get both users' vectors for radar comparison
    cursor_me = await db.execute("SELECT taste_vector FROM users WHERE id=?", (user_id,))
    cursor_other = await db.execute("SELECT taste_vector, name, city, tags FROM users WHERE id=?", (other_id,))
    me = await cursor_me.fetchone()
    other = await cursor_other.fetchone()
    await db.close()

    if not me or not other:
        return {"success": False, "error": {"message": "user not found"}}

    dims = ["spicy", "sweet", "sour", "salty", "umami", "bitter"]
    vec_me = json.loads(me["taste_vector"])
    vec_other = json.loads(other["taste_vector"])

    compare_radar = {
        "me": {dims[i]: round(vec_me[i], 2) for i in range(6)},
        "other": {dims[i]: round(vec_other[i], 2) for i in range(6)},
    }

    shared_dims = [dims[i] for i in range(6) if vec_me[i] > 0.35 and vec_other[i] > 0.35]
    explanation = f"你们在{('、'.join(shared_dims[:3]) if shared_dims else '基础口味')}上有共同信号，适合从可点多种口味的餐厅开始约饭。"
    companion_plan = await meal_companion_skill(user_id, {"other_user_id": other_id})
    joint = {
        "dialogue": [
            {"agent": "A", "content": f"我建议先选{companion_plan.get('restaurant_type', '融合菜')}，双方都更容易点到舒服的菜。"},
            {"agent": "B", "content": companion_plan.get("invite_text", "可以从一顿低压力的饭开始。")},
        ],
        "recommendations": [
            {"restaurant": food, "reason": "来自双方共同口味交集，适合作为第一次约饭候选。"}
            for food in companion_plan.get("shared_foods", [])[:3]
        ],
    }

    return {"success": True, "data": {
        "other_user": {"id": other_id, "name": other["name"], "city": other["city"], "tags": json.loads(other["tags"])},
        "compare_radar": compare_radar,
        "explanation": explanation,
        "agent_dialogue": joint.get("dialogue", []),
        "joint_recommendation": joint.get("recommendations", []),
        "companion_plan": companion_plan,
    }}

import json

import aiosqlite

from config import app_config

DIMS = ["spicy", "sweet", "sour", "salty", "umami", "bitter"]


def _safe_vector(raw: str) -> list[float]:
    try:
        vector = json.loads(raw or "[]")
    except Exception:
        vector = []
    return [(float(v) if isinstance(v, (int, float)) else 0.0) for v in vector]


def _safe_tags(raw: str) -> list[str]:
    try:
        tags = json.loads(raw or "[]")
    except Exception:
        tags = []
    return [str(tag).lower() for tag in tags if tag]


def _fallback_by_profile(me, other) -> dict:
    tags = set(_safe_tags(me["tags"])) | set(_safe_tags(other["tags"]))
    text = " ".join(tags | {str(me["occupation"] or "").lower(), str(other["occupation"] or "").lower()})
    shared = []
    avoid = []

    if any(k in text for k in ["肉", "meat", "protein", "健身", "程序员"]):
        shared.extend(["烤肉", "牛肉饭", "铜锅涮肉"])
    if any(k in text for k in ["辣", "spicy", "重口", "川", "成都"]):
        shared.extend(["川味小炒", "烤鱼", "火锅"])
    if any(k in text for k in ["甜", "sweet", "咖啡", "下午茶"]):
        shared.extend(["甜品咖啡", "下午茶"])
    if any(k in text for k in ["轻食", "控卡", "健康", "fitness"]):
        shared.extend(["轻食饭", "鸡胸肉沙拉"])

    if not shared:
        return {
            "shared_foods": [],
            "avoid": ["双方味觉画像还不完整，第一次约饭建议选择菜品跨度大的餐厅"],
            "invite_text": "我们还需要各自多记录几餐，Agent 才能更准确地推荐饭搭子菜单。",
            "best_scene": "先各自记录 3 餐后再约饭",
            "restaurant_type": "待画像完善",
        }

    city_same = me["city"] and other["city"] and me["city"] == other["city"]
    if not city_same:
        avoid.append("你们所在城市可能不同，先确认可约饭地点")
    avoid.append("当前建议基于标签推断，等双方多记录几餐后会更精准")

    restaurant_type = " / ".join(list(dict.fromkeys(shared))[:2])
    return {
        "shared_foods": list(dict.fromkeys(shared))[:5],
        "avoid": avoid[:3],
        "invite_text": f"你们的公开标签里有共同线索，可以先从 {restaurant_type} 这类选择开始试探。",
        "best_scene": "周末午餐 / 轻松探店",
        "restaurant_type": restaurant_type,
    }


async def meal_companion_skill(user_id: str, params: dict) -> dict:
    other_id = params.get("other_user_id", "")
    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row
    cursor = await db.execute("SELECT id, name, city, occupation, tags, taste_vector FROM users WHERE id=?", (user_id,))
    me = await cursor.fetchone()
    cursor2 = await db.execute("SELECT id, name, city, occupation, tags, taste_vector FROM users WHERE id=?", (other_id,))
    other = await cursor2.fetchone()
    await db.close()

    if not me or not other:
        return {"shared_foods": [], "avoid": [], "invite_text": "", "best_scene": ""}

    vec_me = _safe_vector(me["taste_vector"])
    vec_other = _safe_vector(other["taste_vector"])
    shared = []
    avoid = []

    if len(vec_me) < 14 or len(vec_other) < 14:
        return _fallback_by_profile(me, other)

    avg = [(vec_me[i] + vec_other[i]) / 2 for i in range(6)]
    if avg[4] >= 0.55 or avg[3] >= 0.55:
        shared.extend(["烤肉", "烤鱼", "铜锅涮肉"])
    if avg[0] >= 0.55:
        shared.extend(["火锅", "川味小炒"])
    if avg[1] >= 0.55:
        shared.append("甜品咖啡")
    if not shared:
        shared.extend(["番茄牛腩饭", "鸡汤米线"])

    if abs(vec_me[1] - vec_other[1]) >= 0.35:
        avoid.append("甜品店作为第一次约饭可能不是最佳选择")
    if abs(vec_me[0] - vec_other[0]) >= 0.35:
        avoid.append("辣度需要提前对齐，避免一方吃得太勉强")
    if not avoid:
        avoid.append("第一次约饭建议选择可点多种口味的餐厅，给双方留出选择空间")

    best_scene = "周五晚餐 / 下班后" if max(avg[3], avg[4]) >= 0.55 else "周末午餐 / 轻松探店"
    restaurant_type = "烤肉或火锅" if max(avg[3], avg[4], avg[0]) >= 0.55 else "家常融合菜"
    invite_text = f"系统发现我们在{restaurant_type}上有很高共识，要不要这周找一家店一起吃？"

    return {
        "shared_foods": list(dict.fromkeys(shared))[:5],
        "avoid": avoid[:3],
        "invite_text": invite_text,
        "best_scene": best_scene,
        "restaurant_type": restaurant_type,
    }

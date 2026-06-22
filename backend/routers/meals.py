from fastapi import APIRouter, Request
from models.schemas import MealUpload, ManualMealCreate, MealUpdate
from skills.vision_skill import vision_skill
from skills.vector_skill import vector_skill
from skills.proactive_notify_skill import proactive_notify_skill
from agents import Orchestrator, AgentEvent
from skills import ALL_SKILLS
import json, uuid, aiosqlite, os, base64
from datetime import datetime
from config import app_config
from utils.responses import error_response

router = APIRouter()
orchestrator = Orchestrator(ALL_SKILLS)

MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _to_number(value, default=0):
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        import re
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return default
    return default


def _clean_nutrition(nutrition: dict) -> dict:
    return {
        "calories": _to_number(nutrition.get("calories", 0)),
        "protein": _to_number(nutrition.get("protein", 0)),
        "carbs": _to_number(nutrition.get("carbs", 0)),
        "fat": _to_number(nutrition.get("fat", 0)),
    }


def _clean_description(value: str | None) -> str:
    return (value or "").strip()[:200]


def _read_image_base64(image_path: str) -> str:
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return ""
    return ""


def _image_mime_from_path(image_path: str) -> str:
    ext = os.path.splitext(image_path or "")[1].lower().lstrip(".")
    if ext in ("jpg", "jpeg"):
        return "image/jpeg"
    if ext == "png":
        return "image/png"
    if ext == "webp":
        return "image/webp"
    return "image/jpeg"


def _decode_image(image_base64: str) -> bytes:
    try:
        return base64.b64decode(image_base64, validate=True)
    except Exception:
        raise ValueError("图片数据格式不正确")


def _detect_image_type(img_data: bytes) -> tuple[str, str]:
    if img_data.startswith(b"\xff\xd8\xff"):
        return "jpg", "image/jpeg"
    if img_data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if len(img_data) >= 12 and img_data[:4] == b"RIFF" and img_data[8:12] == b"WEBP":
        return "webp", "image/webp"
    raise ValueError("仅支持 JPG、PNG 或 WebP 图片")


def _validate_image(image_base64: str) -> tuple[bytes, str, str]:
    img_data = _decode_image(image_base64)
    if not img_data:
        raise ValueError("图片不能为空")
    if len(img_data) > MAX_IMAGE_BYTES:
        raise ValueError("图片不能超过 5MB")
    image_ext, mime_type = _detect_image_type(img_data)
    return img_data, image_ext, mime_type


def _clean_text(value: str | None, default: str = "") -> str:
    return (value or default).strip()


def _clean_ingredients(ingredients: list[str] | None) -> list[str]:
    return [item.strip() for item in (ingredients or []) if item and item.strip()][:20]


def _default_taste_tags(ingredients: list[str], description: str) -> dict:
    text = " ".join([*ingredients, description])
    tags = {"salty": 0.45, "sweet": 0.2, "spicy": 0.2, "umami": 0.55, "fresh": 0.35, "oily": 0.35}
    if any(word in text for word in ["辣", "椒", "麻", "川", "湘"]):
        tags["spicy"] = 0.7
        tags["salty"] = 0.55
    if any(word in text for word in ["甜", "糖", "奶", "蛋糕"]):
        tags["sweet"] = 0.65
    if any(word in text for word in ["沙拉", "蔬", "轻", "清淡"]):
        tags["fresh"] = 0.65
        tags["oily"] = 0.2
    if any(word in text for word in ["肉", "牛", "羊", "鸡", "猪", "鱼"]):
        tags["umami"] = 0.7
    return tags


def _default_nutrition(ingredients: list[str]) -> dict:
    text = " ".join(ingredients)
    has_meat = any(word in text for word in ["肉", "牛", "羊", "鸡", "猪", "鱼", "虾"])
    has_staple = any(word in text for word in ["饭", "面", "粉", "饼", "米"])
    return {
        "calories": 560 if has_staple else 420,
        "protein": 28 if has_meat else 16,
        "carbs": 68 if has_staple else 38,
        "fat": 22 if has_meat else 16,
    }


def _row_to_meal_payload(row, include_image: bool = False) -> dict:
    payload = {
        "id": row["id"],
        "user_id": row["user_id"],
        "dish_name": row["dish_name"],
        "cuisine_type": row["cuisine_type"],
        "ingredients": json.loads(row["ingredients"] or "[]"),
        "taste_tags": json.loads(row["taste_tags"] or "{}"),
        "nutrition": json.loads(row["nutrition"] or "{}"),
        "meal_time": row["meal_time"],
        "image_url": row["image_url"],
        "image_mime": _image_mime_from_path(row["image_url"]),
    }
    if include_image:
        payload["image"] = _read_image_base64(row["image_url"])
    return payload


@router.post("")
async def upload_meal(request: Request, body: MealUpload):
    user_id = request.state.user_id

    try:
        img_data, image_ext, mime_type = _validate_image(body.image)
    except ValueError as exc:
        return error_response(str(exc), "BAD_REQUEST")

    user_description = _clean_description(body.description)

    # Direct skill call for speed (Agent orchestration happens async)
    recognition = await vision_skill(user_id, {"image": body.image, "mime_type": mime_type, "description": user_description})
    recognition["user_description"] = user_description

    if not recognition.get("is_food", True):
        return {"success": True, "data": {"is_food": False, "message": recognition.get("message", "未识别到食物，请上传食物照片")}}

    recognition["nutrition"] = _clean_nutrition(recognition.get("nutrition", {}))

    meal_id = f"meal_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()

    # Save image to disk
    os.makedirs(app_config.image_dir, exist_ok=True)
    image_path = os.path.join(app_config.image_dir, f"{meal_id}.{image_ext}")
    with open(image_path, "wb") as f:
        f.write(img_data)

    db = await aiosqlite.connect(app_config.db_path)
    await db.execute(
        "INSERT INTO meals (id, user_id, image_url, dish_name, cuisine_type, ingredients, taste_tags, nutrition, meal_time, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (meal_id, user_id, image_path, recognition.get("dish_name", ""),
         recognition.get("cuisine_type", ""), json.dumps(recognition.get("ingredients", [])),
         json.dumps(recognition.get("taste_tags", {})), json.dumps(recognition.get("nutrition", {})),
         now, now)
    )
    await db.commit()
    await db.close()

    # Update vector
    await vector_skill(user_id, {"action": "compute"})

    meal_payload = {"id": meal_id, **recognition, "meal_time": now, "image_url": image_path, "image_mime": mime_type}

    # Generate micro insight via orchestrator and persist proactive notification
    event = AgentEvent(event_type="meal.uploaded", user_id=user_id, data=recognition)
    result = await orchestrator.process_event(event)
    proactive = await proactive_notify_skill(user_id, {"meal": meal_payload})

    agent_trace = result.data.get("__trace", []) if isinstance(result.data, dict) else []
    return {"success": True, "data": {
        "meal": meal_payload,
        "micro_insight": result.notification or "",
        "proactive_notification": proactive,
        "agent_trace": agent_trace,
    }}


@router.post("/manual")
async def create_manual_meal(request: Request, body: ManualMealCreate):
    user_id = request.state.user_id
    dish_name = _clean_text(body.dish_name)
    if not dish_name:
        return error_response("请填写菜名", "BAD_REQUEST")

    cuisine_type = _clean_text(body.cuisine_type, "家常/未分类") or "家常/未分类"
    ingredients = _clean_ingredients(body.ingredients)
    description = _clean_description(body.description)
    taste_tags = _default_taste_tags(ingredients, description)
    nutrition = _default_nutrition(ingredients)

    meal_id = f"meal_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()
    image_path = ""

    if body.image:
        try:
            img_data, image_ext, _ = _validate_image(body.image)
        except ValueError as exc:
            return error_response(str(exc), "BAD_REQUEST")
        os.makedirs(app_config.image_dir, exist_ok=True)
        image_path = os.path.join(app_config.image_dir, f"{meal_id}.{image_ext}")
        with open(image_path, "wb") as f:
            f.write(img_data)

    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row
    await db.execute(
        "INSERT INTO meals (id, user_id, image_url, dish_name, cuisine_type, ingredients, taste_tags, nutrition, meal_time, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (meal_id, user_id, image_path, dish_name, cuisine_type,
         json.dumps(ingredients, ensure_ascii=False), json.dumps(taste_tags, ensure_ascii=False),
         json.dumps(nutrition, ensure_ascii=False), now, now)
    )
    await db.commit()
    cursor = await db.execute("SELECT * FROM meals WHERE id=? AND user_id=?", (meal_id, user_id))
    row = await cursor.fetchone()
    await db.close()

    await vector_skill(user_id, {"action": "compute"})

    meal_payload = _row_to_meal_payload(row, include_image=bool(image_path))
    meal_payload["user_description"] = description
    meal_payload["manual_created"] = True

    event_data = {**meal_payload, "source": "manual", "manual_created": True}
    micro_insight = "已按你的描述记录这一餐，并同步更新味觉档案。"
    agent_trace = []
    try:
        result = await orchestrator.process_event(AgentEvent(event_type="meal.uploaded", user_id=user_id, data=event_data))
        micro_insight = result.notification or micro_insight
        agent_trace = result.data.get("__trace", []) if isinstance(result.data, dict) else []
    except Exception:
        pass

    proactive = await proactive_notify_skill(user_id, {"meal": meal_payload})
    return {"success": True, "data": {
        "meal": meal_payload,
        "micro_insight": micro_insight,
        "proactive_notification": proactive,
        "agent_trace": agent_trace,
    }}


@router.get("")
async def list_meals(request: Request, page: int = 1, limit: int = 20, date_from: str = "", date_to: str = ""):
    user_id = request.state.user_id
    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row

    query = "SELECT * FROM meals WHERE user_id=?"
    params = [user_id]
    if date_from:
        query += " AND meal_time>=?"
        params.append(date_from)
    if date_to:
        query += " AND meal_time<=?"
        params.append(date_to)
    query += " ORDER BY meal_time DESC LIMIT ? OFFSET ?"
    params.extend([limit, (page - 1) * limit])

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()

    count_cursor = await db.execute("SELECT COUNT(*) FROM meals WHERE user_id=?", (user_id,))
    total = (await count_cursor.fetchone())[0]
    await db.close()

    meals = []
    for r in rows:
        img_path = r["image_url"]
        meals.append({
            "id": r["id"], "dish_name": r["dish_name"], "cuisine_type": r["cuisine_type"],
            "ingredients": json.loads(r["ingredients"]), "taste_tags": json.loads(r["taste_tags"]),
            "nutrition": json.loads(r["nutrition"]), "meal_time": r["meal_time"],
            "has_image": bool(img_path and os.path.exists(img_path)),
        })

    return {"success": True, "data": {"meals": meals, "total": total}}


@router.get("/images")
async def get_meal_images(request: Request, ids: str = ""):
    user_id = request.state.user_id
    meal_ids = [item.strip() for item in ids.split(",") if item.strip()][:30]
    if not meal_ids:
        return {"success": True, "data": {"images": {}}}

    placeholders = ",".join(["?"] * len(meal_ids))
    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute(
        f"SELECT id, image_url FROM meals WHERE user_id=? AND id IN ({placeholders})",
        [user_id, *meal_ids]
    )
    rows = await cursor.fetchall()
    await db.close()

    images = {}
    for meal_id, image_path in rows:
        image_data = _read_image_base64(image_path)
        if image_data:
            images[meal_id] = {"image": image_data, "mime_type": _image_mime_from_path(image_path)}
    return {"success": True, "data": {"images": images}}


@router.put("/{meal_id}")
async def update_meal(meal_id: str, request: Request, body: MealUpdate):
    user_id = request.state.user_id
    dish_name = _clean_text(body.dish_name)
    if not dish_name:
        return error_response("请填写菜名", "BAD_REQUEST")

    cuisine_type = _clean_text(body.cuisine_type, "家常/未分类") or "家常/未分类"
    ingredients = _clean_ingredients(body.ingredients)
    taste_tags = body.taste_tags or _default_taste_tags(ingredients, "")
    nutrition = _clean_nutrition(body.nutrition or _default_nutrition(ingredients))

    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row
    cursor = await db.execute("SELECT * FROM meals WHERE id=?", (meal_id,))
    existing = await cursor.fetchone()
    if not existing:
        await db.close()
        return error_response("meal not found", "NOT_FOUND")
    if existing["user_id"] != user_id:
        await db.close()
        return error_response("not authorized", "FORBIDDEN")

    await db.execute(
        "UPDATE meals SET dish_name=?, cuisine_type=?, ingredients=?, taste_tags=?, nutrition=? WHERE id=?",
        (dish_name, cuisine_type, json.dumps(ingredients, ensure_ascii=False),
         json.dumps(taste_tags, ensure_ascii=False), json.dumps(nutrition, ensure_ascii=False), meal_id)
    )
    await db.commit()
    cursor = await db.execute("SELECT * FROM meals WHERE id=? AND user_id=?", (meal_id, user_id))
    row = await cursor.fetchone()
    await db.close()

    await vector_skill(user_id, {"action": "compute"})
    return {"success": True, "data": {"meal": _row_to_meal_payload(row, include_image=True)}}


@router.get("/{meal_id}")
async def get_meal(meal_id: str, request: Request):
    user_id = request.state.user_id
    db = await aiosqlite.connect(app_config.db_path)
    db.row_factory = aiosqlite.Row
    cursor = await db.execute("SELECT * FROM meals WHERE id=? AND user_id=?", (meal_id, user_id))
    r = await cursor.fetchone()
    await db.close()

    if not r:
        return error_response("not found", "NOT_FOUND")

    return {"success": True, "data": _row_to_meal_payload(r, include_image=True)}


@router.get("/{meal_id}/image")
async def get_meal_image(meal_id: str, request: Request):
    user_id = request.state.user_id
    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute("SELECT image_url FROM meals WHERE id=? AND user_id=?", (meal_id, user_id))
    row = await cursor.fetchone()
    await db.close()

    if not row:
        return error_response("not found", "NOT_FOUND")

    image_data = _read_image_base64(row[0])
    if not image_data:
        return error_response("image not found", "NOT_FOUND")

    return {"success": True, "data": {"image": image_data, "mime_type": _image_mime_from_path(row[0])}}


@router.delete("/{meal_id}")
async def delete_meal(meal_id: str, request: Request):
    user_id = request.state.user_id
    db = await aiosqlite.connect(app_config.db_path)

    # Verify the meal belongs to this user
    cursor = await db.execute("SELECT user_id, image_url FROM meals WHERE id=?", (meal_id,))
    row = await cursor.fetchone()
    if not row:
        await db.close()
        return error_response("meal not found", "NOT_FOUND")
    if row[0] != user_id:
        await db.close()
        return error_response("not authorized", "FORBIDDEN")

    # Delete image file if exists
    img_path = row[1]
    if img_path and os.path.exists(img_path):
        try:
            os.remove(img_path)
        except Exception:
            pass

    # Delete meal record
    await db.execute("DELETE FROM meals WHERE id=?", (meal_id,))
    await db.commit()
    await db.close()

    # Recompute taste vector
    await vector_skill(user_id, {"action": "compute"})

    return {"success": True, "data": {"deleted": meal_id}}

import json
from services import ai_client


async def vision_skill(user_id: str, params: dict) -> dict:
    """调用多模态 AI 识别食物照片，返回结构化信息"""
    image_base64 = params.get("image", "")
    mime_type = params.get("mime_type", "image/jpeg")
    user_description = (params.get("description") or "").strip()[:200]
    if not image_base64:
        return {"error": "no image provided", "is_food": False, "message": "图片不能为空", "description_used": bool(user_description)}

    prompt = f"""分析这张食物照片，并结合用户补充描述，返回JSON格式（不要markdown代码块）。

用户补充描述：{user_description or "无"}

判断原则：
- 请同时参考图片和用户描述。
- 如果图片模糊、遮挡、角度不好或是外卖包装，可以用用户描述补全菜名、食材和口味。
- 如果用户描述与图片明显冲突，以图片为主。
- 不要编造描述中没有、图片也看不出的昂贵食材。
- 图片不是食物时，即使用户描述说是食物，也要谨慎判断，is_food 可以为 false。

返回结构：
{{
    "dish_name": "菜名",
    "cuisine_type": "菜系(川菜/粤菜/湘菜/鲁菜/日料/韩餐/西餐/东南亚)",
    "ingredients": ["主要食材"],
    "taste_tags": {{"spicy": 0-1, "sweet": 0-1, "sour": 0-1, "salty": 0-1, "umami": 0-1, "bitter": 0-1}},
    "nutrition": {{"calories": 数字kcal, "protein": 数字g, "carbs": 数字g, "fat": 数字g}},
    "is_food": true/false,
    "description_used": true/false
}}
如果图片中没有食物，is_food设为false，其他字段可为空。"""

    try:
        raw = await ai_client.vision(image_base64, prompt, mime_type)
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)
    except Exception:
        return {"dish_name": "未识别", "cuisine_type": "未知", "ingredients": [],
                "taste_tags": {"spicy": 0, "sweet": 0, "sour": 0, "salty": 0, "umami": 0, "bitter": 0},
                "nutrition": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0},
                "is_food": False, "description_used": bool(user_description),
                "message": "图片识别服务暂时不可用，请稍后重试"}

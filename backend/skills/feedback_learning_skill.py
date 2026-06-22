import json

import aiosqlite

from config import app_config


def _safe_vector(raw: str) -> list[float]:
    try:
        vector = json.loads(raw or "[]")
    except Exception:
        vector = []
    if not isinstance(vector, list):
        vector = []
    return [(float(v) if isinstance(v, (int, float)) else 0.0) for v in vector]


async def feedback_learning_skill(user_id: str, params: dict) -> dict:
    """Record that feedback affected the user's learning state.

    This is intentionally lightweight: it applies a tiny confidence-style vector nudge
    so user feedback has visible system effect without pretending to train a model.
    """
    accurate = bool(params.get("accurate", True))
    insight_id = params.get("insight_id", "")

    db = await aiosqlite.connect(app_config.db_path)
    cursor = await db.execute("SELECT taste_vector FROM users WHERE id=?", (user_id,))
    row = await cursor.fetchone()
    if not row:
        await db.close()
        return {"updated": False, "learning_summary": "未找到用户画像，暂时无法学习。", "adjustments": []}

    vector = _safe_vector(row[0])
    if len(vector) < 32:
        vector = (vector + [0.3] * 32)[:32]

    adjustments = []
    if accurate:
        # Slightly increase stability/confidence in primary taste dimensions.
        for i in range(6):
            vector[i] = round(min(1, vector[i] + 0.01), 3)
        adjustments.append("提高当前味觉画像置信度")
        learning_summary = "Agent 已记录这次正向反馈，会更信任类似饮食洞察。"
    else:
        # Slightly soften primary taste dimensions to avoid overconfident insights.
        for i in range(6):
            vector[i] = round(max(0, vector[i] - 0.01), 3)
        adjustments.append("降低类似洞察的置信度")
        learning_summary = "Agent 已记录这次负向反馈，会降低类似洞察的判断强度。"

    await db.execute("UPDATE users SET taste_vector=? WHERE id=?", (json.dumps(vector), user_id))
    await db.commit()
    await db.close()

    return {
        "updated": True,
        "insight_id": insight_id,
        "learning_summary": learning_summary,
        "adjustments": adjustments,
    }

import uuid
from datetime import datetime
from agents.memory import AgentMemory


async def notify_skill(user_id: str, params: dict) -> dict:
    """生成并保存通知消息"""
    title = params.get("title", "")
    content = params.get("content", "")
    notify_type = params.get("type", "insight")

    if not title and not content:
        return {"saved": False}

    memory = AgentMemory(user_id)
    await memory.add_short_term(notify_type, title, content)
    return {"saved": True, "id": str(uuid.uuid4())}

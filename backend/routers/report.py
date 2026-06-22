from fastapi import APIRouter, Request
from models.schemas import FeedbackRequest
from skills.report_skill import report_skill
from skills.feedback_learning_skill import feedback_learning_skill
from agents.memory import AgentMemory

router = APIRouter()


@router.get("/weekly")
async def get_weekly_report(request: Request):
    user_id = request.state.user_id
    result = await report_skill(user_id, {})
    return {"success": True, "data": result}


@router.post("/feedback")
async def post_feedback(request: Request, body: FeedbackRequest):
    user_id = request.state.user_id
    memory = AgentMemory(user_id)
    await memory.add_episode("feedback", f"insight {body.insight_id}: {'accurate' if body.accurate else 'inaccurate'}")
    learning = await feedback_learning_skill(user_id, {"insight_id": body.insight_id, "accurate": body.accurate})
    return {"success": True, "data": {"learning": learning}}

from fastapi import APIRouter, Request

from skills.next_meal_skill import next_meal_skill

router = APIRouter()


@router.get("/today")
async def today_recommendation(request: Request):
    result = await next_meal_skill(request.state.user_id, {})
    if result.get("success") is False:
        return result
    return {"success": True, "data": result}

from pydantic import BaseModel
from typing import Optional


class MealUpload(BaseModel):
    image: str  # base64
    description: Optional[str] = None


class ManualMealCreate(BaseModel):
    dish_name: str
    cuisine_type: Optional[str] = None
    ingredients: list[str] = []
    description: Optional[str] = None
    image: Optional[str] = None


class MealUpdate(BaseModel):
    dish_name: str
    cuisine_type: Optional[str] = None
    ingredients: list[str] = []
    taste_tags: Optional[dict[str, float]] = None
    nutrition: Optional[dict[str, float]] = None


class MealResponse(BaseModel):
    id: str
    dish_name: str
    cuisine_type: str
    ingredients: list[str]
    taste_tags: dict[str, float]
    nutrition: dict[str, float]
    meal_time: str
    micro_insight: Optional[str] = None


class TasteProfileResponse(BaseModel):
    radar_data: dict[str, float]
    trends: list[dict]
    predictions: Optional[dict] = None


class WeeklyReportResponse(BaseModel):
    summary: str
    highlights: list[dict]
    reflection: Optional[str] = None


class MatchResponse(BaseModel):
    id: str
    user: dict
    score: float
    dim_scores: dict[str, float]
    common: list[str]
    diff: list[str]
    explanation: Optional[str] = None
    why_recommended: Optional[str] = None
    first_meal_suggestion: Optional[str] = None
    conversation_starter: Optional[str] = None


class MatchActionRequest(BaseModel):
    action: str  # "like" or "skip"


class FeedbackRequest(BaseModel):
    insight_id: str
    accurate: bool


class PrivacyRequest(BaseModel):
    level: str  # "public", "match_only", "private"


class APIResponse(BaseModel):
    success: bool = True
    data: Optional[dict | list] = None
    error: Optional[dict] = None

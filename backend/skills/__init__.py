from skills.vision_skill import vision_skill
from skills.vector_skill import vector_skill
from skills.report_skill import report_skill
from skills.match_skill import match_skill
from skills.trend_skill import trend_skill
from skills.recommend_skill import recommend_skill
from skills.notify_skill import notify_skill
from skills.health_skill import health_skill
from skills.mood_food_skill import mood_food_skill
from skills.feedback_learning_skill import feedback_learning_skill
from skills.memory_timeline_skill import memory_timeline_skill
from skills.next_meal_skill import next_meal_skill
from skills.meal_companion_skill import meal_companion_skill
from skills.city_aggregation_skill import city_aggregation_skill
from skills.restaurant_match_skill import restaurant_match_skill
from skills.proactive_notify_skill import proactive_notify_skill

# Skills organized by agent
TASTE_SKILLS = {
    "vision_skill": vision_skill,
    "vector_skill": vector_skill,
    "report_skill": report_skill,
    "notify_skill": notify_skill,
    "recommend_skill": recommend_skill,
    "health_skill": health_skill,
    "mood_food_skill": mood_food_skill,
    "feedback_learning_skill": feedback_learning_skill,
    "memory_timeline_skill": memory_timeline_skill,
    "next_meal_skill": next_meal_skill,
    "proactive_notify_skill": proactive_notify_skill,
}

SOCIAL_SKILLS = {
    "vector_skill": vector_skill,
    "match_skill": match_skill,
    "recommend_skill": recommend_skill,
    "notify_skill": notify_skill,
    "meal_companion_skill": meal_companion_skill,
}

CITY_SKILLS = {
    "trend_skill": trend_skill,
    "recommend_skill": recommend_skill,
    "notify_skill": notify_skill,
    "city_aggregation_skill": city_aggregation_skill,
    "restaurant_match_skill": restaurant_match_skill,
}

ALL_SKILLS = {
    "taste": TASTE_SKILLS,
    "social": SOCIAL_SKILLS,
    "city": CITY_SKILLS,
}

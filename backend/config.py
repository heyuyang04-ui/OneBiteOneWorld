import os

class AIConfig:
    base_url: str = os.getenv("AI_BASE_URL", "https://oneapi-comate.baidu-int.com/v1")
    api_key: str = os.getenv("AI_API_KEY", "")
    model_name: str = os.getenv("AI_MODEL", "GPT-5.5")

class AppConfig:
    db_path: str = os.getenv("DB_PATH", "demo.db")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "168"))
    image_dir: str = os.getenv("IMAGE_DIR", os.path.join(os.path.dirname(__file__), "data", "images"))
    data_dir: str = os.path.join(os.path.dirname(__file__), "data")

ai_config = AIConfig()
app_config = AppConfig()

# In-memory session store for demo user switching
SESSION = {}

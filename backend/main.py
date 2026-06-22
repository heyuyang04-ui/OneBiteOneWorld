from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import init_db
from routers import meals, profile, report, match, city, notifications, users, recommend, auth
from services.session_store import cleanup_expired_sessions, resolve_session
import json, traceback

app = FastAPI(title="一食万象 API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://172.26.20.173:5173",
        "http://localhost:3000",
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|172\.26\.20\.173):(5173|5174|5175|5176)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] {traceback.format_exc()}")
    return JSONResponse(status_code=500, content={
        "success": False,
        "error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred"}
    })


PUBLIC_API_PATHS = {
    "/api/auth/phone-login",
    "/api/auth/register",
    "/api/users/me/switch",
    "/api/notifications/stream",
}

PUBLIC_PREFIXES = ("/docs", "/redoc")


def _is_public_path(path: str) -> bool:
    return path == "/" or path == "/openapi.json" or path in PUBLIC_API_PATHS or path.startswith(PUBLIC_PREFIXES)


# User identification middleware
@app.middleware("http")
async def user_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    session_id = request.headers.get("X-Session-Id", "")
    user_id = await resolve_session(session_id)
    if user_id:
        request.state.user_id = user_id
        return await call_next(request)

    if _is_public_path(path):
        request.state.user_id = ""
        return await call_next(request)

    if path.startswith("/api"):
        return JSONResponse(status_code=401, content={
            "success": False,
            "error": {"code": "UNAUTHORIZED", "message": "请先登录"}
        })

    request.state.user_id = ""
    return await call_next(request)


# Startup
@app.on_event("startup")
async def startup():
    await init_db()
    await cleanup_expired_sessions()


# Routers
app.include_router(meals.router, prefix="/api/meals", tags=["meals"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(report.router, prefix="/api/report", tags=["report"])
app.include_router(match.router, prefix="/api/match", tags=["match"])
app.include_router(city.router, prefix="/api/city", tags=["city"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["recommend"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api", tags=["users"])


@app.get("/")
async def root():
    return {"message": "一食万象 API", "version": "1.0.0"}

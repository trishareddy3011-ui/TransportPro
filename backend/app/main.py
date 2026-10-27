from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .router import router as api_router
from .routers.supabase_compat import router as supabase_compat_router
from .services.reminder_scheduler import start_reminder_scheduler

app = FastAPI(title="VahanOne API")

# CORS
cors_origins_env = [o.strip() for o in getattr(settings, "cors_origins", "").split(",") if o.strip()]
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost",
]
all_origins = default_origins + cors_origins_env

app.add_middleware(
    CORSMiddleware,
    allow_origins=all_origins if "*" not in cors_origins_env else ["*"],
    allow_origin_regex=r"^https?://([a-zA-Z0-9-]+\.)*(onrender\.com|vercel\.app|netlify\.app|localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Welcome to VahanOne"}


@app.on_event("startup")
def startup_tasks() -> None:
    if settings.enable_reminder_scheduler:
        start_reminder_scheduler()


app.include_router(api_router)
app.include_router(supabase_compat_router)
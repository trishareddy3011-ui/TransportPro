from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/vahanone_db"
    jwt_secret_key: str = "change-this-to-a-secure-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    default_user_role: str = "member"
    admin_role_name: str = "admin"
    enable_reminder_scheduler: bool = False
    reminder_scheduler_interval_minutes: int = 60
    cors_origins: str = "*"
    seed_demo_data: bool = True


settings = Settings()

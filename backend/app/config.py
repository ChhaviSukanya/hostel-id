from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./dev.db"
    secret_key: str = "change-me"
    token_minutes: int = 480
    data_dir: str = "./data"
    cors_origins: str = "http://localhost:5173"
    admin_user_id: str = "admin"
    admin_password: str = ""
    max_image_mb: int = 5
    frontend_dist: str = "../frontend/dist"

    # Google (one department account owns Drive files, Sheets and the Apps Script)
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""
    drive_folder_id: str = ""
    apps_script_url: str = ""
    apps_script_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()

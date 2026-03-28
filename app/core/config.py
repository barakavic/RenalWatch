from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RenalWatch"
    debug: bool = True
    database_url: str = "postgresql+asyncpg://renal:renal123@db:5432/renalwatch"
    at_api_key: str = "your_africas_talking_live_api_key"
    at_username: str = "sandbox"
    smtp_email: str = "your@gmail.com"
    smtp_password: str = "your_gmail_app_password"
    doctor_phone: str = "+254700000000"
    doctor_email: str = "doctor@hospital.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

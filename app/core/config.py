from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RenalWatch"
    debug: bool = True
    database_url: str = "postgresql+asyncpg://renal:renal123@db:5432/renalwatch"
    at_api_key: str = "your_africas_talking_live_api_key"
    at_username: str = "sandbox"
    at_sender_id: str | None = None
    whatsapp_demo_fallback_to_sms: bool = True
    smtp_email: str = Field(
        default="your@gmail.com",
        validation_alias=AliasChoices("SMTP_EMAIL"),
    )
    smtp_password: str = "your_gmail_app_password"
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 465
    smtp_use_ssl: bool = True
    smtp_timeout: int = 15
    email_relay_url: str | None = "http://host.docker.internal:8800/send"
    email_relay_token: str = "renalwatch-demo-relay"
    whatsapp_provider: str = "africastalking"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    chatbot_model_enabled: bool = True
    chatbot_model_name: str = "google/flan-t5-small"
    chatbot_model_max_tokens: int = 40
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.1-8b-instruct:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    doctor_phone: str = "+254700000000"
    doctor_email: str = "doctor@hospital.com"
    wearable_patient_id: int = 1
    renalwatch_api_url: str = "http://api:8000/readings/"
    adb_poll_interval: int = 30
    adb_pull_enabled: bool = True
    fitpro_sync_interval: int = 10
    fitpro_remote_path: str = "/sdcard/Android/data/com.legend.simsonlab.app.android/db/fitPro"
    fitpro_local_path: str = "fitPro.db"

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

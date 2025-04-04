import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    MODEL_NAME: str = Field(default="gpt-3.5-turbo")
    MODEL: str = Field(default_factory=lambda: os.getenv(
        "MODEL", "gpt-3.5-turbo"))

    # WhatsApp Business API
    WHATSAPP_PHONE_ID: str = Field(
        default_factory=lambda: os.getenv("WHATSAPP_PHONE_ID"))
    WHATSAPP_ACCESS_TOKEN: str = Field(
        default_factory=lambda: os.getenv("WHATSAPP_ACCESS_TOKEN"))
    WHATSAPP_RECIPIENT: str = Field(
        default_factory=lambda: os.getenv("WHATSAPP_RECIPIENT", ""))
    VERIFY_TOKEN: str = Field(
        default_factory=lambda: os.getenv("VERIFY_TOKEN"))

    @property
    def URL_SERVIDOR(self) -> str:
        return os.getenv("URL_SERVIDOR", "")

    # Home Assistant
    HOME_ASSISTANT_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("HOME_ASSISTANT_URL"))
    HOME_ASSISTANT_TOKEN: Optional[str] = Field(
        default_factory=lambda: os.getenv("HOME_ASSISTANT_TOKEN"))

    # Redis
    REDIS_URL: str = Field(default_factory=lambda: os.getenv(
        "REDIS_URL", "redis://localhost:6379/0"))

    # Rasa (si lo necesitas)
    RASA_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("RASA_URL"))

    # Database
    DB_HOST: str = Field(
        default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    DB_PORT: int = Field(default_factory=lambda: int(
        os.getenv("DB_PORT", "3306")))
    DB_USER_READER: str = Field(default_factory=lambda: os.getenv(
        "DB_USER_READER", "chatbot_reader"))
    DB_USER_WRITER: str = Field(default_factory=lambda: os.getenv(
        "DB_USER_WRITER", "chatbot_writer"))
    DB_PASS_READER: str = Field(
        default_factory=lambda: os.getenv("DB_PASS_READER", ""))
    DB_PASS_WRITER: str = Field(
        default_factory=lambda: os.getenv("DB_PASS_WRITER", ""))
    DB_NAME: str = Field(
        default_factory=lambda: os.getenv("DB_NAME", "chatbot_db"))

    # Application
    DEBUG: bool = Field(default_factory=lambda: os.getenv(
        "DEBUG", "False").lower() == "true")

    # Configuración del modelo
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Crear instancia de configuración
settings = Settings()

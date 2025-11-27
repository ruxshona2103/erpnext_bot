import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

class TelegramConfig(BaseModel):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    bot_name: str = Field(..., alias="BOT_NAME")
    webhook_url: str|None = Field(None, alias='WEBHOOK_URL')
    webhook_path: str|None = Field(None, alias="WEBHOOK_PATH")


class ERPNextConfig(BaseModel):
    base_url: str = Field(..., alias="ERP_BASE_URL")
    api_key: str = Field(..., alias="ERP_API_KEY")
    api_secret: str = Field(..., alias="ERP_API_SECRET")


class ServerConfig(BaseModel):
    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(8000, alias="PORT")


class SupportConfig(BaseModel):
    """Support contact information for error messages."""
    phone: str = Field("+998 99 123 45 67", alias="SUPPORT_PHONE")
    operator_name: str = Field("Operator", alias="SUPPORT_NAME")


class RedisConfig(BaseModel):
    """Redis configuration for persistent FSM storage."""
    host: str = Field("localhost", alias="REDIS_HOST")
    port: int = Field(6379, alias="REDIS_PORT")
    db: int = Field(0, alias="REDIS_DB")


class Settings(BaseModel):
    telegram: TelegramConfig
    erp: ERPNextConfig
    server: ServerConfig
    redis: RedisConfig
    support: SupportConfig


def load_config() -> Settings:
    """Load and validate config from .env"""

    try:
        telegram = TelegramConfig(
            BOT_TOKEN=os.getenv("BOT_TOKEN"),
            BOT_NAME=os.getenv("BOT_NAME"),
            WEBHOOK_URL=os.getenv("WEBHOOK_URL"),
            WEBHOOK_PATH=os.getenv("WEBHOOK_PATH"),
        )

        erp = ERPNextConfig(
            ERP_BASE_URL=os.getenv("ERP_BASE_URL"),
            ERP_API_KEY=os.getenv("ERP_API_KEY"),
            ERP_API_SECRET=os.getenv("ERP_API_SECRET"),
        )

        server = ServerConfig(
            HOST=os.getenv("HOST"),
            PORT=int(os.getenv("PORT", 8000)),
        )

        redis = RedisConfig(
            REDIS_HOST=os.getenv("REDIS_HOST", "localhost"),
            REDIS_PORT=int(os.getenv("REDIS_PORT", 6379)),
            REDIS_DB=int(os.getenv("REDIS_DB", 0)),
        )

        support = SupportConfig(
            SUPPORT_PHONE=os.getenv("SUPPORT_PHONE", "+998 99 123 45 67"),
            SUPPORT_NAME=os.getenv("SUPPORT_NAME", "Operator"),
        )

        return Settings(telegram=telegram, erp=erp, server=server, redis=redis, support=support)

    except ValidationError as e:
        print("❌ Config validation error:", e)
        raise

config = load_config()

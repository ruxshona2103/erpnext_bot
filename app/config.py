import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

class TelegramConfig(BaseModel):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    bot_name: str = Field(..., alias="BOT_NAME")
    # webhookni sozlash jarayonida ishlatamiz
    webhook_url: str|None = Field(None, alias='WEBHOOK_URL')
    webhook_path: str|None = Field(None, alias="WEBHOOK_PATH")


class ERPNextConfig(BaseModel):
    base_url: str = Field(..., alias="ERP_BASE_URL")
    api_key: str = Field(..., alias="ERP_API_KEY")
    api_secret: str = Field(..., alias="ERP_API_SECRET")


class ServerConfig(BaseModel):
    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(8000, alias="PORT")


class Settings(BaseModel):
    telegram: TelegramConfig
    erp: ERPNextConfig
    server: ServerConfig


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

        return Settings(telegram=telegram, erp=erp, server=server)

    except ValidationError as e:
        print("❌ Config validation error:", e)
        raise

config = load_config()

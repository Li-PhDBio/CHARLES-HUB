"""Configuration loading from .env and environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise ValueError(f"Missing required config: {key}")
    return val


class Config:
    port: int = int(os.getenv("CHARLES_HUB_PORT", "9800"))
    server_host: str = os.getenv("SERVER_HOST", "210.34.84.181")
    hermes_url: str = os.getenv("HERMES_GATEWAY_URL", "http://127.0.0.1:9119")
    feishu_cli_path: str = os.getenv("FEISHU_CLI_PATH", "lark")
    feishu_chat_id: str = _require("FEISHU_CHAT_ID")
    db_path: str = os.getenv("DB_PATH", "data/charles_hub.db")

    @staticmethod
    def bot_profile(name: str) -> tuple[str, str]:
        app_id = _require(f"FEISHU_PROFILE_{name.upper()}_APP_ID")
        secret = _require(f"FEISHU_PROFILE_{name.upper()}_APP_SECRET")
        return app_id, secret


config = Config()

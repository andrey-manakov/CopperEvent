import os
from dataclasses import dataclass
from dotenv import load_dotenv


def load_env() -> None:
    load_dotenv()


@dataclass
class Settings:
    bot_token: str
    log_level: str = "INFO"
    default_tz: str = "UTC"

    @classmethod
    def from_env(cls) -> "Settings":
        load_env()
        bot_token = os.environ.get("BOT_TOKEN", "")
        if not bot_token:
            raise ValueError("BOT_TOKEN is required")
        log_level = os.environ.get("LOG_LEVEL", "INFO")
        default_tz = os.environ.get("TZ", "UTC")
        return cls(bot_token=bot_token, log_level=log_level, default_tz=default_tz)


settings = Settings.from_env()

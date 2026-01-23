from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Yandex.Disk
    YADISK_TOKEN: Optional[str] = None
    YADISK_FOLDER: str

    # URL for posting article metadata
    API_URL: str

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

settings = Settings()
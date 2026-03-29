# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用配置管理，从 .env 文件和环境变量加载设置"""

    def __init__(self):
        self.api_key: str = os.getenv("API_KEY", "") or ""
        self.base_url: str = os.getenv("BASE_URL", "") or "https://api.openai.com/v1"
        self.model: str = os.getenv("MODEL", "") or "gpt-4o"
        interval_str = os.getenv("DEFAULT_INTERVAL", "") or "10"
        self.default_interval: int = int(interval_str)

        jpeg_quality_str = os.getenv("JPEG_QUALITY", "") or "75"
        self.jpeg_quality: int = max(1, min(95, int(jpeg_quality_str)))

        self.reasoning_effort: str | None = os.getenv("REASONING_EFFORT", "") or None

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key.strip())
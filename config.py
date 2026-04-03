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
        try:
            self.default_interval: float = max(0.5, min(300.0, float(interval_str)))
        except ValueError:
            self.default_interval: float = 10.0

        jpeg_quality_str = os.getenv("JPEG_QUALITY", "") or "75"
        try:
            self.jpeg_quality: int = max(1, min(95, int(jpeg_quality_str)))
        except ValueError:
            self.jpeg_quality: int = 75

        self.reasoning_effort: str | None = os.getenv("REASONING_EFFORT", "") or None

        poll_interval_str = os.getenv("STABILITY_POLL_INTERVAL", "") or "200"
        try:
            self.stability_poll_interval: int = max(50, min(2000, int(poll_interval_str)))
        except ValueError:
            self.stability_poll_interval: int = 200

        window_size_str = os.getenv("STABILITY_WINDOW_SIZE", "") or "5"
        try:
            self.stability_window_size: int = max(2, min(20, int(window_size_str)))
        except ValueError:
            self.stability_window_size: int = 5

        threshold_str = os.getenv("STABILITY_THRESHOLD", "") or "3.0"
        try:
            self.stability_threshold: float = max(0.0, min(100.0, float(threshold_str)))
        except ValueError:
            self.stability_threshold: float = 3.0

        change_threshold_str = os.getenv("STABILITY_CHANGE_THRESHOLD", "") or "1.0"
        try:
            self.stability_change_threshold: float = max(0.0, min(100.0, float(change_threshold_str)))
        except ValueError:
            self.stability_change_threshold: float = 1.0

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key.strip())

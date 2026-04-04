# config.py
import logging
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

# 常量定义
MIN_INTERVAL = 0.5  # 最小截图间隔
MAX_INTERVAL = 300.0  # 最大截图间隔
MIN_JPEG_QUALITY = 1  # 最小 JPEG 质量
MAX_JPEG_QUALITY = 95  # 最大 JPEG 质量
MIN_POLL_INTERVAL = 50  # 最小轮询间隔（毫秒）
MAX_POLL_INTERVAL = 2000  # 最大轮询间隔（毫秒）
MIN_WINDOW_SIZE = 2  # 最小窗口大小
MAX_WINDOW_SIZE = 20  # 最大窗口大小


class Config:
    """应用配置管理，从 .env 文件和环境变量加载设置"""

    def __init__(self):
        self.api_key: str = os.getenv("API_KEY", "")
        self.base_url: str = os.getenv("BASE_URL", "")
        self.model: str = os.getenv("MODEL", "")
        interval_str = os.getenv("DEFAULT_INTERVAL", "")
        try:
            self.default_interval: float = max(MIN_INTERVAL, min(MAX_INTERVAL, float(interval_str)))
        except ValueError:
            self.default_interval: float = 10.0

        jpeg_quality_str = os.getenv("JPEG_QUALITY", "")
        try:
            self.jpeg_quality: int = max(MIN_JPEG_QUALITY, min(MAX_JPEG_QUALITY, int(jpeg_quality_str)))
        except ValueError:
            self.jpeg_quality: int = 75

        self.reasoning_effort: str | None = os.getenv("REASONING_EFFORT")

        poll_interval_str = os.getenv("STABILITY_POLL_INTERVAL", "")
        try:
            self.stability_poll_interval: int = max(MIN_POLL_INTERVAL, min(MAX_POLL_INTERVAL, int(poll_interval_str)))
        except ValueError:
            self.stability_poll_interval: int = 200

        window_size_str = os.getenv("STABILITY_WINDOW_SIZE", "")
        try:
            self.stability_window_size: int = max(MIN_WINDOW_SIZE, min(MAX_WINDOW_SIZE, int(window_size_str)))
        except ValueError:
            self.stability_window_size: int = 5

        threshold_str = os.getenv("STABILITY_THRESHOLD", "")
        try:
            self.stability_threshold: float = max(0.0, min(100.0, float(threshold_str)))
        except ValueError:
            self.stability_threshold: float = 3.0

        change_threshold_str = os.getenv("STABILITY_CHANGE_THRESHOLD", "")
        try:
            self.stability_change_threshold: float = max(0.0, min(100.0, float(change_threshold_str)))
        except ValueError:
            self.stability_change_threshold: float = 1.0

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def validate(self) -> list[str]:
        """验证配置完整性，返回错误列表"""
        errors: list[str] = []

        # 验证 API Key
        if not self.has_api_key:
            errors.append("API_KEY is missing or empty")

        # 验证 Model
        if not self.model or not self.model.strip():
            errors.append("MODEL is missing or empty")

        # 验证 Base URL 格式
        if self.base_url:
            if not self.base_url.startswith(("http://", "https://")):
                errors.append(f"BASE_URL format is invalid: {self.base_url}")

        return errors

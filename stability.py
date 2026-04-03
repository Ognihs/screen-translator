# stability.py
"""截图稳定性检测 — 使用 MSE（均方误差）和滑动窗口判断画面是否稳定"""

import collections
import io

import numpy as np
from PIL import Image


class StabilityChecker:
    """截图稳定性检测器

    通过比较相邻两次截图的 MSE 值，配合滑动窗口判断画面是否稳定。
    当滑动窗口内所有 MSE 值都低于阈值时，认为画面稳定。

    Attributes:
        _window_size: 滑动窗口大小
        _mse_threshold: 由 RMSE% 百分比转换而来的 MSE 阈值
        _change_threshold: 内容变化阈值（RMSE%）
        _mse_history: 滑动窗口，存储最近的 MSE 值
        _last_image: 上一次截图的 numpy 数组
        _reference_image: 参考画面（用于内容变化检测）
    """

    def __init__(self, window_size: int, threshold: float, change_threshold: float = 0.0):
        self._window_size = window_size
        self._mse_threshold = (threshold / 100.0 * 255.0) ** 2
        self._change_threshold = change_threshold
        self._mse_history: collections.deque[float] = collections.deque(maxlen=window_size)
        self._last_image: np.ndarray | None = None
        self._reference_image: np.ndarray | None = None

    def reset(self) -> None:
        """清空滑动窗口和历史图片缓存"""
        self._mse_history.clear()
        self._last_image = None

    def reset_reference(self) -> None:
        """清除参考画面，下次 content_changed 调用将返回 True"""
        self._reference_image = None

    def content_changed(self, image_data: bytes) -> bool:
        """检查图片内容是否发生变化。

        首次调用（无参考画面）返回 True。
        后续调用计算与参考画面的 RMSE%，超过阈值返回 True。

        Args:
            image_data: PNG 格式的截图 bytes

        Returns:
            True 表示内容已变化，False 表示内容未变化
        """
        if self._reference_image is None:
            return True

        image = self._decode_image(image_data)
        # 形状不匹配（选区变化），视为内容已变化
        if self._reference_image.shape != image.shape:
            return True
        mse = self._compute_mse(self._reference_image, image)
        rmse_percent = (mse ** 0.5) / 255.0 * 100.0
        return rmse_percent > self._change_threshold

    def update_reference(self, image_data: bytes) -> None:
        """更新参考画面

        Args:
            image_data: PNG 格式的截图 bytes
        """
        self._reference_image = self._decode_image(image_data)

    def check(self, image_data: bytes) -> bool:
        """检查当前截图是否使画面处于稳定状态。

        首次调用时只存储图片，不计算 MSE，返回 False。
        后续调用时与上次截图计算 MSE，追加到滑动窗口，
        当窗口填满且所有 MSE 值都低于阈值时返回 True。

        Args:
            image_data: PNG 格式的截图 bytes

        Returns:
            True 表示画面稳定，False 表示不稳定或窗口未满
        """
        image = self._decode_image(image_data)

        if self._last_image is None:
            self._last_image = image
            return False

        mse = self._compute_mse(self._last_image, image)
        self._last_image = image
        self._mse_history.append(mse)

        if len(self._mse_history) < self._window_size:
            return False

        return all(mse_val <= self._mse_threshold for mse_val in self._mse_history)

    @staticmethod
    def _decode_image(image_data: bytes) -> np.ndarray:
        """将 PNG bytes 解码为 numpy 数组（RGB, float64）

        Args:
            image_data: PNG 格式的图片字节数据

        Returns:
            形状为 (H, W, 3) 的 float64 numpy 数组
        """
        image = Image.open(io.BytesIO(image_data))
        if image.mode != "RGB":
            image = image.convert("RGB")
        return np.array(image, dtype=np.float64)

    @staticmethod
    def _compute_mse(a: np.ndarray, b: np.ndarray) -> float:
        """计算两张图片之间的均方误差（MSE）

        Args:
            a: 第一张图片的 numpy 数组
            b: 第二张图片的 numpy 数组

        Returns:
            MSE 值，范围 0.0 ~ 65025.0
        """
        return float(np.mean((a - b) ** 2))
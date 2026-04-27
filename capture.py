import io
import logging

import mss
import mss.tools
from PIL import Image

logger = logging.getLogger(__name__)


def convert_to_jpeg(png_data: bytes, quality: int = 75) -> bytes:
    """将 PNG 图片数据转换为 JPEG 格式。

    Args:
        png_data: PNG 格式的图片字节数据
        quality: JPEG 压缩质量，范围 1-95

    Returns:
        JPEG 格式的图片字节数据

    Raises:
        ValueError: 当 png_data 为空或 quality 超出范围时
    """
    if not png_data:
        raise ValueError("png_data cannot be empty")
    if not 1 <= quality <= 95:
        raise ValueError("quality must be between 1 and 95")

    try:
        image = Image.open(io.BytesIO(png_data))
    except (IOError, OSError) as e:
        logger.error(f"无效的 PNG 数据，长度: {len(png_data)} bytes, 错误: {e}", exc_info=True)
        raise ValueError(f"Invalid PNG data: {e}") from e

    # 处理带有透明通道的图像（RGBA/LA）或调色板模式（P）
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGB")

    buffer = io.BytesIO()
    try:
        image.save(buffer, format="JPEG", quality=quality)
        jpeg_data = buffer.getvalue()
        logger.debug(f"PNG 转 JPEG 完成，原始大小: {len(png_data)}, JPEG 大小: {len(jpeg_data)}")
        return jpeg_data
    finally:
        buffer.close()


def capture_region(x: int, y: int, width: int, height: int) -> bytes:
    """截取屏幕指定区域

    Args:
        x: 区域左上角 x 坐标
        y: 区域左上角 y 坐标
        width: 区域宽度
        height: 区域高度

    Returns:
        PNG 格式的 bytes 数据

    Raises:
        ValueError: 当 width <= 0 或 height <= 0 时
        RuntimeError: 若 mss.tools.to_png 返回 None
    """
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be greater than 0")

    logger.debug(f"截取屏幕区域: ({x}, {y}) {width}x{height}")
    try:
        with mss.mss() as sct:
            monitor = {
                "left": x,
                "top": y,
                "width": width,
                "height": height,
            }
            screenshot = sct.grab(monitor)
            png_data = mss.tools.to_png(screenshot.rgb, screenshot.size)
            if png_data is None:
                raise RuntimeError("Failed to capture screen region: mss.tools.to_png returned None")
            logger.debug(f"截图完成，大小: {len(png_data)} bytes")
            return png_data
    except Exception as e:
        logger.error(f"截图失败: ({x}, {y}) {width}x{height}, 错误: {e}", exc_info=True)
        raise

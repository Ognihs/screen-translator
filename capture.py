import io

import mss
import mss.tools
from PIL import Image


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
    
    image = Image.open(io.BytesIO(png_data))
    
    # 处理带有透明通道的图像（RGBA/LA）或调色板模式（P）
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGB")
    
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()


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
    """
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be greater than 0")

    with mss.mss() as sct:
        monitor = {
            "left": x,
            "top": y,
            "width": width,
            "height": height,
        }
        screenshot = sct.grab(monitor)
        png_data = mss.tools.to_png(screenshot.rgb, screenshot.size)
        assert png_data is not None
        return png_data

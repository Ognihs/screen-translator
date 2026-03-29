import mss
import mss.tools


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

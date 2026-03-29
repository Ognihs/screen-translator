import pytest
from unittest.mock import patch, MagicMock


def test_capture_region_returns_bytes():
    """测试截取区域返回 PNG bytes"""
    from capture import capture_region

    mock_screenshot = MagicMock()
    mock_screenshot.rgb = b"fake rgb data"
    mock_screenshot.size = (300, 400)

    with patch("capture.mss") as mock_mss, patch("capture.mss.tools.to_png") as mock_to_png:
        mock_instance = MagicMock()
        mock_instance.grab.return_value = mock_screenshot
        mock_mss.mss.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_mss.mss.return_value.__exit__ = MagicMock(return_value=False)
        mock_to_png.return_value = b"\x89PNG\r\n\x1a\n fake png data"

        result = capture_region(100, 200, 300, 400)
        assert isinstance(result, bytes)
        assert result == b"\x89PNG\r\n\x1a\n fake png data"

        # 验证 grab 被正确调用
        mock_instance.grab.assert_called_once()
        call_args = mock_instance.grab.call_args[0][0]
        assert call_args["left"] == 100
        assert call_args["top"] == 200
        assert call_args["width"] == 300
        assert call_args["height"] == 400

        # 验证 to_png 被正确调用
        mock_to_png.assert_called_once_with(b"fake rgb data", (300, 400))


def test_capture_region_invalid_size():
    """测试无效尺寸抛出异常"""
    from capture import capture_region

    with pytest.raises(ValueError):
        capture_region(0, 0, 0, 0)

    with pytest.raises(ValueError):
        capture_region(0, 0, -10, 100)


def test_convert_to_jpeg_basic():
    """测试基本的 PNG 到 JPEG 转换"""
    from capture import convert_to_jpeg
    from PIL import Image
    import io
    
    # 创建一个简单的 PNG 图像
    img = Image.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    png_data = buffer.getvalue()
    
    jpeg_data = convert_to_jpeg(png_data, quality=75)
    
    assert isinstance(jpeg_data, bytes)
    assert len(jpeg_data) > 0
    # JPEG 文件以 FF D8 FF 开头
    assert jpeg_data[:3] == b'\xff\xd8\xff'


def test_convert_to_jpeg_with_alpha():
    """测试带透明通道的 PNG 转换"""
    from capture import convert_to_jpeg
    from PIL import Image
    import io
    
    # 创建一个带透明通道的 RGBA 图像
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    png_data = buffer.getvalue()
    
    jpeg_data = convert_to_jpeg(png_data, quality=75)
    
    assert isinstance(jpeg_data, bytes)
    assert len(jpeg_data) > 0
    assert jpeg_data[:3] == b'\xff\xd8\xff'


def test_convert_to_jpeg_quality_affects_size():
    """测试不同质量参数影响文件大小"""
    from capture import convert_to_jpeg
    from PIL import Image
    import io
    
    # 创建一个有细节的图像
    img = Image.new("RGB", (200, 200), color="blue")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    png_data = buffer.getvalue()
    
    low_quality = convert_to_jpeg(png_data, quality=10)
    high_quality = convert_to_jpeg(png_data, quality=95)
    
    # 低质量应该比高质量文件更小
    assert len(low_quality) < len(high_quality)


def test_convert_to_jpeg_invalid_empty_data():
    """测试空数据抛出异常"""
    from capture import convert_to_jpeg
    
    with pytest.raises(ValueError, match="png_data cannot be empty"):
        convert_to_jpeg(b"")


def test_convert_to_jpeg_invalid_quality():
    """测试无效质量参数抛出异常"""
    from capture import convert_to_jpeg
    from PIL import Image
    import io
    
    img = Image.new("RGB", (10, 10), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    png_data = buffer.getvalue()
    
    with pytest.raises(ValueError, match="quality must be between 1 and 95"):
        convert_to_jpeg(png_data, quality=0)
    
    with pytest.raises(ValueError, match="quality must be between 1 and 95"):
        convert_to_jpeg(png_data, quality=100)

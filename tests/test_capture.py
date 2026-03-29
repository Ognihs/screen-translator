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

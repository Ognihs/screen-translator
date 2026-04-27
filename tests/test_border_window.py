# tests/test_border_window.py
"""border_window.py 单元测试"""

import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt


@pytest.mark.usefixtures("qtbot")
class TestBorderWindowInitialization:
    """BorderWindow 初始化测试"""

    def test_window_constants(self):
        """测试窗口常量定义"""
        from border_window import BorderWindow

        assert BorderWindow.BORDER_WIDTH == 3
        assert BorderWindow.BORDER_COLOR.red() == 0
        assert BorderWindow.BORDER_COLOR.green() == 255
        assert BorderWindow.BORDER_COLOR.blue() == 0

    def test_initialization_with_defaults(self, qtbot):
        """测试默认初始化"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        # 验证初始状态
        assert window._region.isNull()
        assert not window.isVisible()

    def test_initialization_with_parent(self, qtbot):
        """测试带父窗口的初始化"""
        from border_window import BorderWindow

        parent = QWidget()
        qtbot.addWidget(parent)

        window = BorderWindow(parent=parent)
        qtbot.addWidget(window)

        assert window.parent() == parent

    def test_region_initially_empty(self, qtbot):
        """测试区域初始为空"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)
        assert window._region.isNull()


@pytest.mark.usefixtures("qtbot")
class TestWindowFlags:
    """窗口标志测试"""

    def test_window_has_frameless_flag(self, qtbot):
        """测试窗口无边框标志"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        flags = window.windowFlags()
        assert flags & Qt.WindowType.FramelessWindowHint

    def test_window_has_stays_on_top_flag(self, qtbot):
        """测试窗口置顶标志"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        flags = window.windowFlags()
        assert flags & Qt.WindowType.WindowStaysOnTopHint

    def test_window_has_transparent_for_input_flag(self, qtbot):
        """测试窗口鼠标穿透标志"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        flags = window.windowFlags()
        assert flags & Qt.WindowType.WindowTransparentForInput

    def test_window_has_tool_flag(self, qtbot):
        """测试窗口工具窗口标志"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        flags = window.windowFlags()
        assert flags & Qt.WindowType.Tool

    def test_window_has_translucent_background(self, qtbot):
        """测试窗口透明背景属性"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        assert window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


@pytest.mark.usefixtures("qtbot")
class TestSetRegion:
    """set_region() 方法测试"""

    def test_set_region_updates_internal_region(self, qtbot):
        """测试 set_region 更新内部区域"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        window.set_region(100, 200, 300, 400)

        assert window._region.x() == 100
        assert window._region.y() == 200
        assert window._region.width() == 300
        assert window._region.height() == 400

    def test_set_region_sets_geometry(self, qtbot):
        """测试 set_region 设置窗口几何位置"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        window.set_region(100, 200, 300, 400)

        assert window.x() == 100
        assert window.y() == 200
        assert window.width() == 300
        assert window.height() == 400

    def test_set_region_shows_window(self, qtbot):
        """测试 set_region 显示窗口"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        assert not window.isVisible()
        window.set_region(0, 0, 100, 100)
        assert window.isVisible()

    def test_set_region_with_zero_dimensions(self, qtbot):
        """测试 set_region 拒绝零尺寸输入"""
        from border_window import BorderWindow
        import pytest

        window = BorderWindow()
        qtbot.addWidget(window)

        with pytest.raises(ValueError, match="width and height must be positive"):
            window.set_region(0, 0, 0, 0)

    def test_set_region_with_negative_dimensions(self, qtbot):
        """测试 set_region 拒绝负尺寸输入"""
        from border_window import BorderWindow
        import pytest

        window = BorderWindow()
        qtbot.addWidget(window)

        with pytest.raises(ValueError, match="width and height must be positive"):
            window.set_region(100, 100, -50, -50)


@pytest.mark.usefixtures("qtbot")
class TestClearRegion:
    """clear_region() 方法测试"""

    def test_clear_region_resets_region(self, qtbot):
        """测试 clear_region 重置区域"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        # 先设置区域
        window.set_region(100, 200, 300, 400)
        assert not window._region.isNull()

        # 清除区域
        window.clear_region()
        assert window._region.isNull()

    def test_clear_region_hides_window(self, qtbot):
        """测试 clear_region 隐藏窗口"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        # 先设置区域显示窗口
        window.set_region(100, 200, 300, 400)
        assert window.isVisible()

        # 清除区域
        window.clear_region()
        assert not window.isVisible()

    def test_clear_region_on_empty_region(self, qtbot):
        """测试 clear_region 处理空区域"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        # 初始就是空区域
        window.clear_region()

        assert window._region.isNull()
        assert not window.isVisible()


@pytest.mark.usefixtures("qtbot")
class TestPaintEvent:
    """paintEvent 绘制测试"""

    def test_paint_event_with_null_region_does_nothing(self, qtbot):
        """测试空区域时不绘制"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        # 模拟 paintEvent
        mock_event = MagicMock()
        result = window.paintEvent(mock_event)

        # paintEvent 返回 None，但应该正常执行
        assert result is None
        mock_event.assert_not_called()

    def test_paint_event_with_valid_region(self, qtbot):
        """测试有效区域时绘制"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        window.set_region(10, 10, 100, 100)

        # 模拟 paintEvent
        mock_event = MagicMock()
        result = window.paintEvent(mock_event)

        assert result is None


@pytest.mark.usefixtures("qtbot")
class TestBorderDimensions:
    """边框尺寸验证测试"""

    def test_border_width_constant(self, qtbot):
        """测试边框宽度常量"""
        from border_window import BorderWindow

        assert isinstance(BorderWindow.BORDER_WIDTH, int)
        assert BorderWindow.BORDER_WIDTH > 0

    def test_border_color_constant(self, qtbot):
        """测试边框颜色常量"""
        from border_window import BorderWindow

        color = BorderWindow.BORDER_COLOR
        assert color.red() == 0
        assert color.green() == 255
        assert color.blue() == 0

    def test_small_region_paint_calculation(self, qtbot):
        """测试小区域绘制计算"""
        from border_window import BorderWindow

        window = BorderWindow()
        qtbot.addWidget(window)

        # 设置极小区域
        window.set_region(0, 0, 1, 1)

        # 获取绘制参数
        draw_width = window._region.width() - BorderWindow.BORDER_WIDTH
        draw_height = window._region.height() - BorderWindow.BORDER_WIDTH

        # 即使区域很小，调整计算仍应正确
        assert draw_width == 1 - BorderWindow.BORDER_WIDTH
        assert draw_height == 1 - BorderWindow.BORDER_WIDTH

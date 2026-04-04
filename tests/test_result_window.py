# tests/test_result_window.py
"""result_window.py 单元测试"""

import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent, QKeyEvent


@pytest.mark.usefixtures("qtbot")
class TestResultWindowInitialization:
    """ResultWindow 初始化测试"""

    def test_window_constants(self):
        """测试窗口常量定义"""
        from result_window import ResultWindow
        
        assert ResultWindow.BG_COLOR == "#1e1e1e"
        assert ResultWindow.TITLE_BG_COLOR == "#2d2d2d"
        assert ResultWindow.TEXT_COLOR == "#d4d4d4"
        assert ResultWindow.BORDER_COLOR == "#3c3c3c"
        assert ResultWindow.TITLE_HEIGHT == 32
        assert ResultWindow.SIZE_GRIP_SIZE == 16

    def test_initialization_with_defaults(self, qtbot):
        """测试默认初始化"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        
        # 验证初始状态
        assert window._drag_position is None
        assert window._size_grip is not None
        assert not window.isVisible()

    def test_initialization_with_parent(self, qtbot):
        """测试带父窗口的初始化"""
        from result_window import ResultWindow
        from PySide6.QtWidgets import QWidget
        
        parent = QWidget()
        qtbot.addWidget(parent)
        
        window = ResultWindow(parent=parent)
        qtbot.addWidget(window)
        
        assert window.parent() == parent

    def test_drag_position_initially_none(self, qtbot):
        """测试拖动位置初始为 None"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        assert window._drag_position is None


@pytest.mark.usefixtures("qtbot")
class TestSetText:
    """set_text() 方法测试"""

    def test_set_text_updates_text_edit(self, qtbot):
        """测试 set_text 更新文本编辑区"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        
        test_text = "测试翻译结果"
        window.set_text(test_text)
        
        assert window._text_edit.toPlainText() == test_text

    def test_set_text_shows_window(self, qtbot):
        """测试 set_text 显示窗口"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        
        assert not window.isVisible()
        window.set_text("翻译文本")
        assert window.isVisible()

    def test_set_text_with_empty_string(self, qtbot):
        """测试设置空字符串"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        
        window.set_text("")
        
        assert window._text_edit.toPlainText() == ""

    def test_set_text_with_multiline_content(self, qtbot):
        """测试设置多行内容"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        
        multiline_text = "第一行\n第二行\n第三行"
        window.set_text(multiline_text)
        
        assert window._text_edit.toPlainText() == multiline_text


@pytest.mark.usefixtures("qtbot")
class TestClearText:
    """clear_text() 方法测试"""

    def test_clear_text_clears_text_edit(self, qtbot):
        """测试 clear_text 清除文本编辑区"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        
        window.set_text("翻译文本")
        window.clear_text()
        
        assert window._text_edit.toPlainText() == ""

    def test_clear_text_hides_window(self, qtbot):
        """测试 clear_text 隐藏窗口"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        
        window.set_text("翻译文本")
        assert window.isVisible()
        
        window.clear_text()
        
        assert not window.isVisible()


@pytest.mark.usefixtures("qtbot")
class TestWindowDrag:
    """窗口拖动功能测试"""

    def test_mouse_press_event_starts_drag(self, qtbot):
        """测试鼠标按下开始拖动"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        window.show()
        
        # 在标题栏区域内按下鼠标
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(16, 16),  # 标题栏内
            QPoint(16, 16),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        window.mousePressEvent(event)
        
        # _drag_position 应该被设置
        assert window._drag_position is not None

    def test_mouse_press_event_ignores_right_button(self, qtbot):
        """测试鼠标右键不触发拖动"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(16, 16),
            QPoint(16, 16),
            Qt.MouseButton.RightButton,  # 右键
            Qt.MouseButton.RightButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        window.mousePressEvent(event)
        
        assert window._drag_position is None

    def test_mouse_press_event_ignores_outside_title_bar(self, qtbot):
        """测试标题栏区域外不触发拖动"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        
        # y > TITLE_HEIGHT (32)
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(16, 50),  # 标题栏外
            QPoint(16, 50),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        window.mousePressEvent(event)
        
        assert window._drag_position is None

    def test_mouse_move_event_drags_window(self, qtbot):
        """测试鼠标移动拖动窗口"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        window.show()
        
        # 先按下开始拖动
        press_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(16, 16),
            QPoint(16, 16),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        window.mousePressEvent(press_event)
        
        # 记录初始位置
        initial_pos = window.pos()
        
        # 移动鼠标
        move_event = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            QPoint(116, 116),
            QPoint(116, 116),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        window.mouseMoveEvent(move_event)
        
        # 窗口位置应该改变
        assert window.pos() != initial_pos

    def test_mouse_move_event_ignores_without_drag_position(self, qtbot):
        """测试无拖动位置时不移动窗口"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        window.show()
        
        initial_pos = window.pos()
        
        # 没有先按下鼠标，直接移动
        move_event = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            QPoint(116, 116),
            QPoint(116, 116),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        window.mouseMoveEvent(move_event)
        
        # 窗口位置不应改变
        assert window.pos() == initial_pos

    def test_mouse_release_event_stops_drag(self, qtbot):
        """测试鼠标释放停止拖动"""
        from result_window import ResultWindow
        
        window = ResultWindow()
        qtbot.addWidget(window)
        window.show()
        
        # 开始拖动
        press_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(16, 16),
            QPoint(16, 16),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        window.mousePressEvent(press_event)
        assert window._drag_position is not None
        
        # 释放鼠标
        release_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonRelease,
            QPoint(16, 16),
            QPoint(16, 16),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        window.mouseReleaseEvent(release_event)
        
        # _drag_position 应该被清除
        assert window._drag_position is None


@pytest.mark.usefixtures("qtbot")
class TestResizeEvent:
    """窗口大小调整事件测试"""

    def test_resize_event_updates_size_grip_position(self, qtbot):
        """测试 resizeEvent 更新大小调整手柄位置"""
        from result_window import ResultWindow
        from PySide6.QtGui import QResizeEvent
        
        window = ResultWindow()
        qtbot.addWidget(window)
        window.show()
        
        # 初始 size grip 位置
        assert window._size_grip is not None
        initial_x = window._size_grip.x()
        initial_y = window._size_grip.y()
        
        # 调整窗口大小
        window.resize(600, 500)
        
        # size grip 应该移动到新位置
        assert window._size_grip is not None
        assert window._size_grip.x() != initial_x or window._size_grip.y() != initial_y


@pytest.mark.usefixtures("qtbot")
class TestCloseEvent:
    """closeEvent() 方法测试"""

    def test_close_event_hides_window(self, qtbot):
        """测试 closeEvent 隐藏而非销毁窗口"""
        from result_window import ResultWindow

        window = ResultWindow()
        qtbot.addWidget(window)
        window.show()
        assert window.isVisible()

        window.close()
        assert not window.isVisible()  # 窗口应被隐藏而非销毁

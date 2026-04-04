# tests/test_selector.py
"""selector.py 单元测试"""

import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QPoint, QRect, Qt


@pytest.mark.usefixtures("qtbot")
class TestSelectionOverlay:
    """SelectionOverlay 选区选择器测试"""

    def test_normal_initialization(self):
        """测试正常选区创建"""
        from selector import SelectionOverlay
        
        overlay = SelectionOverlay()

        # 验证初始化状态
        assert overlay._start_pos is None
        assert overlay._end_pos is None
        assert overlay._selection_rect is None

        # 验证信号存在
        assert hasattr(overlay, "selection_made")
        assert hasattr(overlay, "selection_cancelled")

    def test_esc_key_cancels_selection(self):
        """测试 ESC 键取消选区"""
        from selector import SelectionOverlay
        from PySide6.QtGui import QKeyEvent

        overlay = SelectionOverlay()

        # 模拟选区过程中的 ESC 按键
        with patch.object(overlay, "selection_cancelled") as mock_cancelled, \
             patch.object(overlay, "close") as mock_close:
            
            # 创建真实的 ESC 按键事件
            event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)

            overlay.keyPressEvent(event)

            # 验证取消信号被发出
            mock_cancelled.emit.assert_called_once()
            # 验证窗口被关闭
            mock_close.assert_called_once()

    def test_selection_too_small_emits_cancelled(self):
        """测试选区过小时触发取消信号"""
        from selector import SelectionOverlay
        from PySide6.QtCore import QPoint
        from PySide6.QtGui import QMouseEvent

        overlay = SelectionOverlay()

        # 设置选区起点（小选区）
        overlay._start_pos = QPoint(100, 100)
        overlay._end_pos = QPoint(105, 105)  # 宽度只有5，小于10

        # 模拟鼠标释放事件
        with patch.object(overlay, "selection_cancelled") as mock_cancelled, \
             patch.object(overlay, "close") as mock_close:
            
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonRelease,
                QPoint(105, 105),
                QPoint(105, 105),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )

            overlay.mouseReleaseEvent(event)

            # 验证取消信号被发出（而非 selection_made）
            mock_cancelled.emit.assert_called_once()
            mock_close.assert_called_once()

    def test_valid_selection_emits_selection_made(self):
        """测试有效选区发出 selection_made 信号"""
        from selector import SelectionOverlay
        from PySide6.QtCore import QPoint
        from PySide6.QtGui import QMouseEvent

        overlay = SelectionOverlay()

        # 设置有效选区
        overlay._start_pos = QPoint(100, 100)
        overlay._end_pos = QPoint(200, 200)  # 宽度100，大于10

        with patch.object(overlay, "selection_made") as mock_made, \
             patch.object(overlay, "close") as mock_close:
            
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonRelease,
                QPoint(200, 200),
                QPoint(200, 200),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )

            overlay.mouseReleaseEvent(event)

            # 验证 selection_made 信号被发出
            mock_made.emit.assert_called_once()
            # 验证窗口被关闭
            mock_close.assert_called_once()

    def test_window_properties_validated(self):
        """测试窗口属性验证"""
        from selector import SelectionOverlay
        from PySide6.QtCore import Qt

        with patch("selector.QWidget.setWindowFlags") as mock_set_flags, \
             patch("selector.QWidget.setAttribute") as mock_set_attr, \
             patch("selector.QWidget.setCursor") as mock_set_cursor:
            
            overlay = SelectionOverlay()

            # 验证窗口标志设置
            mock_set_flags.assert_called_once()
            call_args = mock_set_flags.call_args[0][0]
            # 检查必要的窗口标志
            assert Qt.WindowType.FramelessWindowHint in call_args
            assert Qt.WindowType.WindowStaysOnTopHint in call_args
            assert Qt.WindowType.Tool in call_args

            # 验证透明背景属性
            mock_set_attr.assert_called_with(Qt.WidgetAttribute.WA_TranslucentBackground)

            # 验证十字光标
            mock_set_cursor.assert_called_with(Qt.CursorShape.CrossCursor)

    def test_show_and_select_resets_state(self):
        """测试 show_and_select 重置状态"""
        from selector import SelectionOverlay

        overlay = SelectionOverlay()
        
        # 预先设置一些状态
        overlay._start_pos = QPoint(100, 100)
        overlay._end_pos = QPoint(200, 200)
        overlay._selection_rect = QRect(100, 100, 100, 100)

        with patch.object(overlay, "show") as mock_show, \
             patch.object(overlay, "activateWindow") as mock_activate:
            
            overlay.show_and_select()

            # 验证状态被重置
            assert overlay._start_pos is None
            assert overlay._end_pos is None
            assert overlay._selection_rect is None

            # 验证窗口显示
            mock_show.assert_called_once()
            mock_activate.assert_called_once()

    def test_mouse_move_updates_selection_rect(self):
        """测试鼠标移动更新选区矩形"""
        from selector import SelectionOverlay
        from PySide6.QtCore import QPoint
        from PySide6.QtGui import QMouseEvent

        overlay = SelectionOverlay()
        
        # 设置起始位置
        overlay._start_pos = QPoint(100, 100)

        with patch.object(overlay, "update") as mock_update:
            event = QMouseEvent(
                QMouseEvent.Type.MouseMove,
                QPoint(200, 200),
                QPoint(200, 200),
                Qt.MouseButton.NoButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )

            overlay.mouseMoveEvent(event)

            # 验证选区矩形已更新
            assert overlay._selection_rect is not None
            mock_update.assert_called()

    def test_mouse_press_records_start_position(self):
        """测试鼠标按下记录起始位置"""
        from selector import SelectionOverlay
        from PySide6.QtCore import QPoint
        from PySide6.QtGui import QMouseEvent

        overlay = SelectionOverlay()
        
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(100, 100),
            QPoint(100, 100),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )

        overlay.mousePressEvent(event)

        # 验证起始位置被记录
        assert overlay._start_pos is not None
        assert overlay._end_pos is not None
        assert overlay._selection_rect is None

    def test_non_esc_key_propagates(self):
        """测试非 ESC 键事件传递给父类"""
        from selector import SelectionOverlay
        from PySide6.QtGui import QKeyEvent

        overlay = SelectionOverlay()

        with patch.object(overlay, "selection_cancelled") as mock_cancelled:
            # 创建非 ESC 按键事件
            event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)

            overlay.keyPressEvent(event)

            # 验证取消信号未被发出
            mock_cancelled.emit.assert_not_called()

    def test_selection_threshold_10_pixels(self):
        """测试选区阈值验证（宽高必须 >= 10）"""
        from selector import SelectionOverlay
        from PySide6.QtCore import QPoint
        from PySide6.QtGui import QMouseEvent

        overlay = SelectionOverlay()

        # 测试宽度刚好为阈值（10）
        overlay._start_pos = QPoint(0, 0)
        overlay._end_pos = QPoint(10, 100)

        with patch.object(overlay, "selection_made") as mock_made, \
             patch.object(overlay, "close") as mock_close:
            
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonRelease,
                QPoint(10, 100),
                QPoint(10, 100),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )

            overlay.mouseReleaseEvent(event)

            # 宽度10 >= 10，高度100 >= 10，应该发出 selection_made
            mock_made.emit.assert_called_once()

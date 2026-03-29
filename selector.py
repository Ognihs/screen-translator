# selector.py
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QWidget, QApplication


class SelectionOverlay(QWidget):
    """全屏透明遮罩，用于鼠标拖拽选择屏幕区域"""

    selection_made = Signal(int, int, int, int)  # x, y, width, height
    selection_cancelled = Signal()

    def __init__(self):
        super().__init__()
        self._start_pos = None
        self._end_pos = None
        self._selection_rect = None
        self._setup_ui()

    def _setup_ui(self):
        """设置全屏透明遮罩窗口"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # 覆盖所有屏幕的虚拟桌面
        screens = QApplication.screens()
        if screens:
            self.setGeometry(screens[0].virtualGeometry())

    def show_and_select(self):
        """显示遮罩并等待用户选择"""
        self._start_pos = None
        self._end_pos = None
        self._selection_rect = None
        self.show()
        self.activateWindow()

    def keyPressEvent(self, event):
        """ESC 键取消选区"""
        if event.key() == Qt.Key.Key_Escape:
            self.selection_cancelled.emit()
            self.close()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """记录鼠标按下位置"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.globalPosition().toPoint()
            self._end_pos = self._start_pos
            self._selection_rect = None

    def mouseMoveEvent(self, event):
        """实时更新选区矩形"""
        if self._start_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._end_pos = event.globalPosition().toPoint()
            self._selection_rect = QRect(self._start_pos, self._end_pos).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放，确认选区"""
        if event.button() == Qt.MouseButton.LeftButton and self._start_pos is not None:
            self._end_pos = event.globalPosition().toPoint()
            rect = QRect(self._start_pos, self._end_pos).normalized()
            self.close()
            if rect.width() >= 10 and rect.height() >= 10:
                self.selection_made.emit(rect.x(), rect.y(), rect.width(), rect.height())
            else:
                self.selection_cancelled.emit()

    def paintEvent(self, event):
        """绘制半透明遮罩和选区矩形"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 半透明黑色遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        # 选区矩形
        if self._selection_rect is not None:
            # 清除选区内的遮罩（透明）
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self._selection_rect, Qt.GlobalColor.transparent)

            # 绘制蓝色虚线边框
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            pen = QPen(QColor(0, 120, 215), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(self._selection_rect)

        painter.end()

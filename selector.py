# selector.py
import logging

logger = logging.getLogger(__name__)

from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QPen, QColor, QKeyEvent, QMouseEvent, QPaintEvent
from PySide6.QtWidgets import QWidget, QApplication

# 常量定义
MIN_SELECTION_SIZE = 10  # 最小选区大小（像素）
MASK_ALPHA = 100  # 遮罩透明度
BORDER_COLOR = QColor(0, 120, 215)  # 边框颜色（蓝色）
BORDER_WIDTH = 2  # 边框宽度


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

        # 覆盖所有屏幕的虚拟桌面 - 计算所有屏幕的联合几何区域
        screens = QApplication.screens()
        if screens:
            # 计算所有屏幕的联合边界矩形
            min_x = min(screen.geometry().x() for screen in screens)
            min_y = min(screen.geometry().y() for screen in screens)
            max_x = max(screen.geometry().right() for screen in screens)
            max_y = max(screen.geometry().bottom() for screen in screens)
            self.setGeometry(QRect(min_x, min_y, max_x - min_x, max_y - min_y))

    def show_and_select(self):
        """显示遮罩并等待用户选择"""
        self._start_pos = None
        self._end_pos = None
        self._selection_rect = None
        self.show()
        self.activateWindow()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """ESC 键取消选区"""
        if event.key() == Qt.Key.Key_Escape:
            self.selection_cancelled.emit()
            self.close()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """记录鼠标按下位置"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = event.globalPosition().toPoint()
            self._end_pos = self._start_pos
            self._selection_rect = None

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """实时更新选区矩形"""
        if self._start_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._end_pos = event.globalPosition().toPoint()
            self._selection_rect = QRect(self._start_pos, self._end_pos).normalized()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """鼠标释放，确认选区"""
        if event.button() == Qt.MouseButton.LeftButton and self._start_pos is not None:
            self._end_pos = event.globalPosition().toPoint()
            rect = QRect(self._start_pos, self._end_pos).normalized()
            self.close()
            if rect.width() >= MIN_SELECTION_SIZE and rect.height() >= MIN_SELECTION_SIZE:
                self.selection_made.emit(rect.x(), rect.y(), rect.width(), rect.height())
            else:
                self.selection_cancelled.emit()

    def paintEvent(self, event: QPaintEvent) -> None:
        """绘制半透明遮罩和选区矩形"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 半透明黑色遮罩
            painter.fillRect(self.rect(), QColor(0, 0, 0, MASK_ALPHA))

            # 选区矩形
            if self._selection_rect is not None:
                # 清除选区内的遮罩（透明）
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                painter.fillRect(self._selection_rect, Qt.GlobalColor.transparent)

                # 绘制蓝色虚线边框
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                pen = QPen(BORDER_COLOR, BORDER_WIDTH, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawRect(self._selection_rect)
        finally:
            painter.end()

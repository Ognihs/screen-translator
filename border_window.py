"""选区边框窗口 — 在选区边缘显示绿色边框"""

import logging

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPen, QColor, QPaintEvent

logger = logging.getLogger(__name__)

# 常量定义
CORNER_RADIUS = 8  # 圆角半径


class BorderWindow(QWidget):
    """选区边框窗口，无边框置顶，显示 3px 绿色边框"""

    BORDER_COLOR = QColor(0, 255, 0)  # 绿色
    BORDER_WIDTH = 3

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._region = QRect()
        self._init_ui()

    def _init_ui(self):
        """初始化窗口属性"""
        # 无边框置顶窗口，鼠标穿透
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.Tool
        )
        # 窗口透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 初始隐藏
        self.hide()

    def set_region(self, x: int, y: int, width: int, height: int) -> None:
        """设置边框位置和大小

        Args:
            x: 选区左上角 x 坐标
            y: 选区左上角 y 坐标
            width: 选区宽度
            height: 选区高度

        Raises:
            ValueError: 当 width 或 height 不为正值时
        """
        if width <= 0 or height <= 0:
            raise ValueError(f"width and height must be positive, got width={width}, height={height}")
        self._region = QRect(x, y, width, height)
        self.setGeometry(self._region)
        self.show()

    def clear_region(self) -> None:
        """清除边框，隐藏窗口"""
        self._region = QRect()
        self.hide()

    def paintEvent(self, event: QPaintEvent) -> None:
        """绘制绿色边框"""
        if self._region.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(self.BORDER_COLOR, self.BORDER_WIDTH)
        painter.setPen(pen)

        # 绘制矩形边框，略微调整以完整显示边框
        adjust = self.BORDER_WIDTH // 2
        painter.drawRoundedRect(
            adjust,
            adjust,
            self._region.width() - self.BORDER_WIDTH,
            self._region.height() - self.BORDER_WIDTH,
            CORNER_RADIUS,
            CORNER_RADIUS,  # xRadius, yRadius
        )

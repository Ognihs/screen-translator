"""翻译结果窗口 — 置顶无边框窗口，显示翻译文本"""

import logging

from PySide6.QtWidgets import QWidget, QTextEdit, QSizeGrip, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent, QResizeEvent, QCloseEvent

logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_WIDTH = 400  # 默认宽度
DEFAULT_HEIGHT = 300  # 默认高度
MIN_WIDTH = 200  # 最小宽度
MIN_HEIGHT = 150  # 最小高度


class ResultWindow(QWidget):
    """翻译结果窗口，置顶无边框，包含自定义标题栏和可调整大小的文本显示区"""

    # 暗色主题颜色
    BG_COLOR = "#1e1e1e"
    TITLE_BG_COLOR = "#2d2d2d"
    TEXT_COLOR = "#d4d4d4"
    BORDER_COLOR = "#3c3c3c"
    TITLE_HEIGHT = 32
    SIZE_GRIP_SIZE = 16

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._drag_position: QPoint | None = None
        self._size_grip: QSizeGrip | None = None
        self._init_ui()

    def _init_ui(self):
        """初始化窗口 UI"""
        # 置顶无边框窗口，使用 Tool 标志避免在任务栏显示
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        # 初始窗口大小和最小尺寸
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        # 暗色主题背景
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.BG_COLOR};
                color: {self.TEXT_COLOR};
                border: 1px solid {self.BORDER_COLOR};
            }}
        """)
        # 窗口透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 自定义标题栏
        title_bar = QWidget()
        title_bar.setFixedHeight(self.TITLE_HEIGHT)
        title_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {self.TITLE_BG_COLOR};
                border: none;
                border-bottom: 1px solid {self.BORDER_COLOR};
            }}
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(8, 0, 8, 0)
        title_layout.setSpacing(4)

        # 标题标签
        title_label = QLabel("翻译结果")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {self.TEXT_COLOR};
                background-color: transparent;
                font-size: 13px;
            }}
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        main_layout.addWidget(title_bar)

        # 文本显示区
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.BG_COLOR};
                color: {self.TEXT_COLOR};
                border: none;
                padding: 8px;
                font-size: 14px;
                selection-background-color: #264f78;
            }}
        """)
        self._text_edit.setPlaceholderText("翻译结果将在此显示...")
        main_layout.addWidget(self._text_edit)

        # 右下角大小调整手柄
        self._size_grip = QSizeGrip(self)
        self._size_grip.setStyleSheet("""
            QSizeGrip {
                background-color: transparent;
            }
            QSizeGrip:hover {
                background-color: rgba(255, 255, 255, 10);
            }
        """)
        # 显式设置 QSizeGrip 初始位置
        self._size_grip.move(self.width() - self.SIZE_GRIP_SIZE, self.height() - self.SIZE_GRIP_SIZE)
        self._size_grip.resize(self.SIZE_GRIP_SIZE, self.SIZE_GRIP_SIZE)

        # 初始隐藏
        self.hide()

    def resizeEvent(self, event: QResizeEvent):
        """窗口大小改变时更新 QSizeGrip 位置"""
        if self._size_grip is not None:
            self._size_grip.move(self.width() - self.SIZE_GRIP_SIZE, self.height() - self.SIZE_GRIP_SIZE)
            self._size_grip.resize(self.SIZE_GRIP_SIZE, self.SIZE_GRIP_SIZE)
        super().resizeEvent(event)

    def set_text(self, text: str):
        """设置翻译文本

        Args:
            text: 翻译文本内容
        """
        self._text_edit.setPlainText(text)
        self.show()

    def clear_text(self):
        """清除翻译文本"""
        self._text_edit.clear()
        self.hide()

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件，用于开始拖动窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 检查是否在标题栏区域（上方 32 像素）
            if event.position().y() <= self.TITLE_HEIGHT:
                self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件，用于拖动窗口"""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_position is not None:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件，停止拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = None
            event.accept()

    def closeEvent(self, event: QCloseEvent):
        """窗口关闭事件处理，隐藏而非销毁窗口"""
        event.ignore()
        self.hide()

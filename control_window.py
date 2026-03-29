# control_window.py
"""主控制面板 — 应用的核心协调者，集成所有模块"""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QSpinBox,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PySide6.QtGui import QCloseEvent

from config import Config
from capture import capture_region
from translator import translate_image
from selector import SelectionOverlay
from border_window import BorderWindow
from result_window import ResultWindow


class ControlWindow(QWidget):
    """主控制面板，协调所有模块"""

    # 状态枚举
    class State:
        READY = "就绪"
        RUNNING = "运行中"
        PAUSED = "已暂停"
        TRANSLATING = "翻译中..."

    def __init__(self):
        super().__init__()
        self._config = Config()
        self._state = self.State.READY
        self._selection = None  # (x, y, width, height)
        self._is_translating = False  # 防止翻译重叠

        # 子窗口
        self._border_window = BorderWindow()
        self._result_window = ResultWindow()
        self._selection_overlay = None

        # 定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)

        self._init_ui()
        self._update_button_states()
        self._check_api_key()

    def _init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("Screen Translator")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # 源语言/目标语言
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("源语言:"))
        self._source_lang_combo = QComboBox()
        self._source_lang_combo.addItems(["中文", "日语", "英语"])
        self._source_lang_combo.setCurrentText("日语")  # 默认源语言为日语
        lang_layout.addWidget(self._source_lang_combo)

        lang_layout.addWidget(QLabel("目标语言:"))
        self._target_lang_combo = QComboBox()
        self._target_lang_combo.addItems(["中文", "日语", "英语"])
        self._target_lang_combo.setCurrentText("中文")  # 默认目标语言为中文
        lang_layout.addWidget(self._target_lang_combo)
        lang_layout.addStretch()
        layout.addLayout(lang_layout)

        # 截图间隔
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("截图间隔:"))
        self._interval_spin = QSpinBox()
        self._interval_spin.setSuffix(" 秒")
        self._interval_spin.setMinimum(1)
        self._interval_spin.setMaximum(300)
        self._interval_spin.setValue(self._config.default_interval)
        interval_layout.addWidget(self._interval_spin)
        interval_layout.addStretch()
        layout.addLayout(interval_layout)

        # API 地址
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("API地址:"))
        self._api_url_edit = QLineEdit()
        self._api_url_edit.setText(self._config.base_url)
        self._api_url_edit.setPlaceholderText("https://api.openai.com/v1")
        api_layout.addWidget(self._api_url_edit, 1)
        layout.addLayout(api_layout)

        # 模型
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型:"))
        self._model_edit = QLineEdit()
        self._model_edit.setText(self._config.model)
        self._model_edit.setPlaceholderText("gpt-4o")
        model_layout.addWidget(self._model_edit, 1)
        layout.addLayout(model_layout)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self._select_btn = QPushButton("选择区域")
        self._select_btn.clicked.connect(self._on_select_region)
        btn_layout.addWidget(self._select_btn)

        self._start_btn = QPushButton("开始")
        self._start_btn.clicked.connect(self._on_start)
        btn_layout.addWidget(self._start_btn)

        self._pause_btn = QPushButton("暂停")
        self._pause_btn.clicked.connect(self._on_pause)
        btn_layout.addWidget(self._pause_btn)

        self._stop_btn = QPushButton("停止")
        self._stop_btn.clicked.connect(self._on_stop)
        btn_layout.addWidget(self._stop_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

        # 状态栏
        self._status_label = QLabel("状态: 就绪")
        layout.addWidget(self._status_label)

    def _check_api_key(self):
        """检查 API Key 是否配置"""
        if not self._config.has_api_key:
            self._set_status("请配置 API Key")
            self._start_btn.setEnabled(False)

    def _set_status(self, message: str):
        """更新状态栏"""
        self._status_label.setText(f"状态: {message}")

    def _update_button_states(self):
        """根据当前状态更新按钮启用状态"""
        is_ready = self._state == self.State.READY
        is_running = self._state == self.State.RUNNING
        is_paused = self._state == self.State.PAUSED

        self._select_btn.setEnabled(is_ready)
        # 开始按钮：就绪时可启动，暂停时可恢复
        self._start_btn.setEnabled(
            (is_ready and self._selection is not None and self._config.has_api_key)
            or is_paused
        )
        self._pause_btn.setEnabled(is_running)
        self._pause_btn.setText("暂停" if is_running else "继续")
        self._stop_btn.setEnabled(is_running or is_paused)

        # 运行/暂停时禁用配置控件
        self._source_lang_combo.setEnabled(is_ready)
        self._target_lang_combo.setEnabled(is_ready)
        self._interval_spin.setEnabled(is_ready)
        self._api_url_edit.setEnabled(is_ready)
        self._model_edit.setEnabled(is_ready)

    def _set_state(self, new_state: str):
        """设置新状态"""
        self._state = new_state
        self._set_status(new_state)
        self._update_button_states()

    def _on_select_region(self):
        """选择区域按钮点击"""
        if self._state != self.State.READY:
            return

        self._selection_overlay = SelectionOverlay()
        self._selection_overlay.selection_made.connect(self._on_selection_made)
        self._selection_overlay.selection_cancelled.connect(self._on_selection_cancelled)
        self._selection_overlay.show_and_select()

    def _on_selection_made(self, x: int, y: int, width: int, height: int):
        """选区完成"""
        if width < 10 or height < 10:
            QMessageBox.warning(self, "选区过小", "选区过小，请重新选择")
            self._selection = None
            self._border_window.clear_region()
            return

        self._selection = (x, y, width, height)
        self._border_window.set_region(x, y, width, height)
        self._set_status(f"已选择区域: {width}x{height}")
        self._update_button_states()

    def _on_selection_cancelled(self):
        """选区取消"""
        self._selection = None
        self._border_window.clear_region()
        self._set_status("已取消选择")
        self._update_button_states()

    def _on_start(self):
        """开始按钮点击（也用于从暂停恢复）"""
        if self._state == self.State.PAUSED:
            # 从暂停恢复
            self._state = self.State.RUNNING
            self._result_window.clear_text()
            self._start_timer()
            self._set_status("运行中")
            self._update_button_states()
            return

        if self._state != self.State.READY:
            return

        if self._selection is None:
            QMessageBox.warning(self, "未选择区域", "请先选择截图区域")
            return

        if not self._config.has_api_key:
            QMessageBox.warning(self, "API Key 未配置", "请配置 API Key")
            return

        # 启动定时器，首次翻译由定时器自然触发
        self._state = self.State.RUNNING
        self._start_timer()
        self._set_status("运行中")
        self._update_button_states()

    def _on_pause(self):
        """暂停/继续按钮点击"""
        if self._state == self.State.RUNNING:
            self._timer.stop()
            self._state = self.State.PAUSED
            self._set_status("已暂停")
            self._update_button_states()
        elif self._state == self.State.PAUSED:
            self._state = self.State.RUNNING
            self._result_window.clear_text()
            self._start_timer()
            self._set_status("运行中")
            self._update_button_states()

    def _start_timer(self):
        """启动定时器"""
        interval_ms = self._interval_spin.value() * 1000
        self._timer.start(interval_ms)

    def _on_stop(self):
        """停止按钮点击"""
        self._timer.stop()
        self._selection = None
        self._border_window.clear_region()
        self._result_window.clear_text()
        self._set_state(self.State.READY)

    def _on_timer_tick(self):
        """定时器触发"""
        if self._state != self.State.RUNNING:
            return
        
        # 如果上一次翻译还在进行，跳过本次
        if self._is_translating:
            return

        self._execute_translation()

    def _execute_translation(self):
        """执行截图和翻译"""
        if self._selection is None:
            return

        self._is_translating = True
        self._set_status(self.State.TRANSLATING)

        x, y, width, height = self._selection

        try:
            # 截图
            image_data = capture_region(x, y, width, height)

            # 获取语言参数
            source_lang = self._source_lang_combo.currentText()
            target_lang = self._target_lang_combo.currentText()

            # 翻译（使用用户配置的参数，有 fallback）
            result = translate_image(
                image_data=image_data,
                source_lang=source_lang,
                target_lang=target_lang,
                api_key=self._config.api_key,
                base_url=self._api_url_edit.text().strip() or self._config.base_url,
                model=self._model_edit.text().strip() or self._config.model,
            )

            # 显示结果
            if self._result_window.isHidden():
                self._result_window.show()
            self._result_window.set_text(result)

            # 检查是否包含错误前缀
            if result.startswith("错误："):
                self._set_status(result)
            else:
                self._set_status(self.State.RUNNING)

        except Exception as e:
            self._set_status(f"错误：{type(e).__name__} — {e}")
        finally:
            self._is_translating = False

    def closeEvent(self, event: QCloseEvent):
        """窗口关闭事件"""
        self._timer.stop()
        self._border_window.close()
        if self._result_window is not None:
            self._result_window.close()
        if self._selection_overlay is not None:
            self._selection_overlay.close()
        event.accept()

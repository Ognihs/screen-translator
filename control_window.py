# control_window.py
"""主控制面板 — 应用的核心协调者，集成所有模块"""

import logging
import time
from enum import StrEnum

from PySide6.QtCore import QTimer, QThread, Signal, QPoint
from PySide6.QtGui import QCloseEvent, QGuiApplication, QMouseEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QMessageBox,
)

from openai import OpenAI

from config import Config, MIN_INTERVAL, MAX_INTERVAL
from capture import capture_region, convert_to_jpeg
from translator import translate_image, ReasoningEffort
from selector import SelectionOverlay
from border_window import BorderWindow
from result_window import ResultWindow
from stability import StabilityChecker

# 支持的语言列表
SUPPORTED_LANGUAGES = ["中文", "日语", "英语"]

# 常量定义
MIN_SELECTION_SIZE = 10  # 最小选区大小（像素）

# 模块级日志记录器
logger = logging.getLogger(__name__)


class State(StrEnum):
    """应用状态枚举"""
    READY = "就绪"
    RUNNING = "运行中"
    PAUSED = "已暂停"
    TRANSLATING = "翻译中..."


class TranslationWorker(QThread):
    """后台翻译线程，避免阻塞主线程"""

    # 信号：翻译完成时发送结果
    translation_completed = Signal(str)
    # 信号：翻译失败时发送错误信息
    translation_failed = Signal(str)

    def __init__(self, image_data: bytes, source_lang: str, target_lang: str,
                 model: str, reasoning_effort: ReasoningEffort | None = None,
                 client: OpenAI | None = None):
        super().__init__()
        self._image_data = image_data
        self._source_lang = source_lang
        self._target_lang = target_lang
        self._model = model
        self._reasoning_effort: ReasoningEffort | None = reasoning_effort
        self._client = client
        self._cancelled = False  # 取消标志

    def cancel(self) -> None:
        """请求取消翻译（协作式取消）"""
        self._cancelled = True

    def run(self):
        """在后台线程中执行翻译"""
        try:
            result = translate_image(
                image_data=self._image_data,
                source_lang=self._source_lang,
                target_lang=self._target_lang,
                api_key="",
                base_url="",
                model=self._model,
                reasoning_effort=self._reasoning_effort,
                client=self._client,
            )
            # 如果已取消，不发送结果
            if self._cancelled:
                return
            # 通过结构化结果判断成功/失败
            if result.is_error:
                self.translation_failed.emit(result.text)
            else:
                self.translation_completed.emit(result.text)
        except Exception as e:
            # 如果已取消，不发送错误信息
            if not self._cancelled:
                self.translation_failed.emit(f"错误：{type(e).__name__} — {e}")


class ControlWindow(QWidget):
    """主控制面板，协调所有模块"""

    def __init__(self):
        super().__init__()
        self._config = Config()
        self._state = State.READY
        self._selection = None  # (x, y, width, height)
        self._is_translating = False  # 防止翻译重叠
        self._translation_worker = None  # 后台翻译线程
        self._api_client: OpenAI | None = None  # 复用的 API 客户端
        self._api_client_url: str = ""  # 上次创建客户端时的 base_url

        # 子窗口
        self._border_window = BorderWindow()
        self._result_window = ResultWindow()
        self._selection_overlay = None

        # 稳定性轮询定时器
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._on_poll_tick)

        # 稳定性检测器
        self._stability_checker = StabilityChecker(
            window_size=self._config.stability_window_size,
            threshold=self._config.stability_threshold,
            change_threshold=self._config.stability_change_threshold,
        )

        # 上次翻译完成时间（用于间隔约束）
        self._last_translation_time: float = 0.0

        # 上次截图数据（用于内容变化检测）
        self._last_screenshot_data: bytes | None = None

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
        self._source_lang_combo.addItems(SUPPORTED_LANGUAGES)
        self._source_lang_combo.setCurrentText("日语")  # 默认源语言为日语
        lang_layout.addWidget(self._source_lang_combo)

        lang_layout.addWidget(QLabel("目标语言:"))
        self._target_lang_combo = QComboBox()
        self._target_lang_combo.addItems(SUPPORTED_LANGUAGES)
        self._target_lang_combo.setCurrentText("中文")  # 默认目标语言为中文
        lang_layout.addWidget(self._target_lang_combo)
        lang_layout.addStretch()
        layout.addLayout(lang_layout)

        # 截图间隔
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("截图间隔:"))
        self._interval_spin = QDoubleSpinBox()
        self._interval_spin.setSuffix(" 秒")
        self._interval_spin.setDecimals(1)
        self._interval_spin.setSingleStep(0.5)
        self._interval_spin.setMinimum(MIN_INTERVAL)
        self._interval_spin.setMaximum(MAX_INTERVAL)
        self._interval_spin.setValue(self._config.default_interval)
        self._interval_spin.lineEdit().setReadOnly(True)
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

        # 推理深度
        reasoning_layout = QHBoxLayout()
        reasoning_layout.addWidget(QLabel("推理深度:"))
        self._reasoning_combo = QComboBox()
        self._reasoning_items: list[tuple[str, ReasoningEffort | None]] = [
            ("默认", None),
            ("关闭", "none"),
            ("低", "low"),
            ("中", "medium"),
            ("高", "high"),
        ]
        for text, _ in self._reasoning_items:
            self._reasoning_combo.addItem(text)
        # 从配置读取默认值
        if self._config.reasoning_effort:
            for i, (_, value) in enumerate(self._reasoning_items):
                if value == self._config.reasoning_effort:
                    self._reasoning_combo.setCurrentIndex(i)
                    break
        reasoning_layout.addWidget(self._reasoning_combo)
        reasoning_layout.addStretch()
        layout.addLayout(reasoning_layout)

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
        logger.info("检查 API Key 配置")
        if not self._config.has_api_key:
            logger.warning("API Key 未配置")
            self._set_status("请配置 API Key")
            self._start_btn.setEnabled(False)
        else:
            logger.info("API Key 已配置")

    def _set_status(self, message: str):
        """更新状态栏"""
        self._status_label.setText(f"状态: {message}")

    def _update_button_states(self):
        """根据当前状态更新按钮启用状态"""
        is_ready = self._state == State.READY
        is_running = self._state == State.RUNNING
        is_paused = self._state == State.PAUSED

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
        self._reasoning_combo.setEnabled(is_ready)

    def _set_state(self, new_state: State):
        """设置新状态"""
        logger.info(f"状态转换: {self._state} -> {new_state}")
        self._state = new_state
        self._set_status(new_state)
        self._update_button_states()

    def _on_select_region(self) -> None:
        """选择区域按钮点击"""
        if self._state != State.READY:
            return

        self._selection_overlay = SelectionOverlay()
        self._selection_overlay.selection_made.connect(self._on_selection_made)
        self._selection_overlay.selection_cancelled.connect(self._on_selection_cancelled)
        self._selection_overlay.show_and_select()

    def _on_selection_made(self, x: int, y: int, width: int, height: int) -> None:
        """选区完成"""
        logger.info(f"选区完成: ({x}, {y}) {width}x{height}")
        if width < MIN_SELECTION_SIZE or height < MIN_SELECTION_SIZE:
            logger.warning(f"选区过小: {width}x{height}")
            QMessageBox.warning(self, "选区过小", "选区过小，请重新选择")
            self._selection = None
            self._border_window.clear_region()
            return

        self._selection = (x, y, width, height)
        self._border_window.set_region(x, y, width, height)
        self._set_status(f"已选择区域: {width}x{height}")
        self._update_button_states()

    def _on_selection_cancelled(self) -> None:
        """选区取消"""
        self._selection = None
        self._border_window.clear_region()
        self._set_status("已取消选择")
        self._update_button_states()

    def _on_start(self) -> None:
        """开始按钮点击（也用于从暂停恢复）"""
        logger.info("开始按钮点击")
        if self._state == State.PAUSED:
            # 从暂停恢复，跳过验证
            logger.info("从暂停状态恢复")
            pass
        elif self._state == State.READY:
            if self._selection is None:
                logger.warning("未选择区域，无法启动")
                QMessageBox.warning(self, "未选择区域", "请先选择截图区域")
                return
            if not self._config.has_api_key:
                logger.warning("API Key 未配置，无法启动")
                QMessageBox.warning(self, "API Key 未配置", "请配置 API Key")
                return
        else:
            return

        # 统一的启动/恢复逻辑
        self._set_state(State.RUNNING)
        self._start_timer()
        self._stability_checker.reset()
        self._last_translation_time = 0.0
        self._result_window.set_text("等待画面稳定...")

    def _on_pause(self) -> None:
        """暂停按钮点击"""
        logger.info("暂停按钮点击")
        if self._state == State.RUNNING:
            self._pause_translation()

    def _start_timer(self):
        """启动稳定性轮询定时器"""
        self._poll_timer.start(self._config.stability_poll_interval)

    def _pause_translation(self):
        """暂停翻译"""
        self._poll_timer.stop()
        self._cancel_current_worker()
        self._set_state(State.PAUSED)

    def _on_stop(self) -> None:
        """停止按钮点击"""
        logger.info("停止按钮点击")
        self._poll_timer.stop()
        self._cancel_current_worker()
        self._selection = None
        self._border_window.clear_region()
        self._result_window.clear_text()
        self._stability_checker.reset_reference()
        self._set_state(State.READY)

    def _cancel_current_worker(self):
        """取消当前正在运行的翻译线程"""
        if self._translation_worker is not None and self._translation_worker.isRunning():
            # 请求取消
            self._translation_worker.cancel()
            # 断开信号连接，忽略后续结果
            try:
                self._translation_worker.translation_completed.disconnect(self._on_translation_completed)
                self._translation_worker.translation_failed.disconnect(self._on_translation_failed)
                self._translation_worker.finished.disconnect(self._on_translation_finished)
            except RuntimeError:
                pass  # 信号已断开或对象已销毁
            self._is_translating = False

    def _on_poll_tick(self):
        """稳定性轮询定时器触发"""
        if self._state != State.RUNNING:
            return

        # 如果上一次翻译还在进行，跳过本次
        if self._is_translating:
            return

        if self._selection is None:
            return

        x, y, width, height = self._selection

        # 获取屏幕 DPR，将逻辑像素转换为物理像素
        dpr = 1.0
        screen = QGuiApplication.screenAt(QPoint(x, y))
        if screen:
            dpr = screen.devicePixelRatio()

        physical_x = round(x * dpr)
        physical_y = round(y * dpr)
        physical_width = round(width * dpr)
        physical_height = round(height * dpr)

        try:
            screenshot_data = capture_region(physical_x, physical_y, physical_width, physical_height)
            is_stable = self._stability_checker.check(screenshot_data)
        except Exception as e:
            logger.error(f"截图或稳定性检测失败: {e}", exc_info=True)
            self._set_status("截图失败，等待重试...")
            return  # 截图或解码失败，跳过本次轮询

        if not is_stable:
            return

        # 保存截图数据用于内容变化检测和后续更新参考画面
        self._last_screenshot_data = screenshot_data

        # 内容变化检测
        if not self._stability_checker.content_changed(screenshot_data):
            return

        # 检查翻译间隔约束
        now = time.monotonic()
        min_interval = self._interval_spin.value()
        if now - self._last_translation_time < min_interval:
            return

        # 画面稳定且满足间隔约束，执行翻译
        image_data = convert_to_jpeg(screenshot_data, self._config.jpeg_quality)
        self._do_translate(image_data)

    def _do_translate(self, image_data: bytes):
        """执行翻译（由稳定性检测触发）"""
        logger.info("翻译开始")
        self._is_translating = True
        self._set_status(State.TRANSLATING)

        # 获取语言参数
        source_lang = self._source_lang_combo.currentText()
        target_lang = self._target_lang_combo.currentText()

        # 获取推理深度
        reasoning_index = self._reasoning_combo.currentIndex()
        reasoning_effort = self._reasoning_items[reasoning_index][1]

        # 获取或创建复用的 API 客户端
        base_url = self._api_url_edit.text().strip() or self._config.base_url
        api_key = self._config.api_key
        if not api_key:
            logger.error("API Key 为空，请检查配置")
            self._set_status("错误：API Key 未设置")
            self._is_translating = False
            return

        if self._api_client is None or self._api_client_url != base_url:
            logger.info(f"创建新的 API 客户端，base_url: {base_url}")
            self._api_client = OpenAI(
                api_key=api_key, base_url=base_url
            )
            self._api_client_url = base_url

        # 创建后台翻译线程
        self._translation_worker = TranslationWorker(
            image_data=image_data,
            source_lang=source_lang,
            target_lang=target_lang,
            model=self._model_edit.text().strip() or self._config.model,
            reasoning_effort=reasoning_effort,
            client=self._api_client,
        )

        # 连接信号
        self._translation_worker.translation_completed.connect(self._on_translation_completed)
        self._translation_worker.translation_failed.connect(self._on_translation_failed)
        self._translation_worker.finished.connect(self._on_translation_finished)

        # 启动后台线程
        logger.info(f"启动翻译线程: {source_lang} -> {target_lang}")
        self._translation_worker.start()

    def _post_translation_cleanup(self, status_msg: str):
        """翻译后清理（公共方法，供成功和失败回调共用）"""
        self._last_translation_time = time.monotonic()
        self._stability_checker.reset()
        # 更新参考画面
        if self._last_screenshot_data is not None:
            self._stability_checker.update_reference(self._last_screenshot_data)
        # 仅在运行状态下更新状态，暂停时保持暂停状态
        if self._state == State.RUNNING:
            self._set_status(status_msg)

    def _on_translation_completed(self, result: str):
        """翻译完成回调（在主线程执行）"""
        logger.info("翻译完成")
        self._post_translation_cleanup(State.RUNNING)
        # 显示结果
        if self._result_window.isHidden():
            self._result_window.show()
        self._result_window.set_text(result)

    def _on_translation_failed(self, error_msg: str):
        """翻译失败回调（在主线程执行）"""
        logger.error(f"翻译失败: {error_msg}")
        self._post_translation_cleanup(error_msg)

    def _on_translation_finished(self):
        """翻译线程结束回调（在主线程执行）"""
        self._is_translating = False

    def mousePressEvent(self, event: QMouseEvent):
        """点击空白区域时清除焦点"""
        focused = self.focusWidget()
        if focused:
            focused.clearFocus()
        super().mousePressEvent(event)

    def closeEvent(self, event: QCloseEvent):
        """窗口关闭事件"""
        self._poll_timer.stop()
        self._cancel_current_worker()
        self._border_window.close()
        if self._result_window is not None:
            self._result_window.close()
        if self._selection_overlay is not None:
            self._selection_overlay.close()
        event.accept()

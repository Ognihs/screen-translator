# AGENTS.md — Screen Translator

## 环境与命令

- **Python 3.14+**（`.python-version` 锁定 `3.14`）
- **包管理器：uv**（不是 pip）
- 安装依赖：`uv sync`
- 运行应用：`uv run python main.py`
- 运行全部测试：`uv run pytest tests/ -v`
- 运行单个测试文件：`uv run pytest tests/test_config.py -v`

## 代码质量工具

- 格式化：`uv run ruff format .`
- lint 检查：`uv run ruff check .`
- lint 自动修复：`uv run ruff check --fix .`
- 类型检查：`uv run pyright`
- 推荐验证顺序：`uv run ruff format . ; uv run ruff check . ; uv run pyright ; uv run pytest tests/ -v`

## 依赖

- PySide6 — GUI 框架
- mss — 屏幕截图
- openai — OpenAI 兼容 API 客户端
- numpy + Pillow — 稳定性检测中的图像处理
- python-dotenv — 环境变量加载
- 开发依赖：pytest、pytest-qt（Qt 信号/槽测试）、ruff、pyright

## 环境变量

- 必须从 `.env.example` 复制到 `.env`
- 必填：`API_KEY`、`MODEL`
- 可选：`BASE_URL`（默认 OpenAI）、`DEFAULT_INTERVAL`（秒）、`JPEG_QUALITY`（1-95）、`REASONING_EFFORT`（none/low/medium/high）、`STABILITY_POLL_INTERVAL`（ms）、`STABILITY_WINDOW_SIZE`、`STABILITY_THRESHOLD`（RMSE%）、`STABILITY_CHANGE_THRESHOLD`（RMSE%）、`LOG_LEVEL`
- `config.py` 在**模块导入时**调用 `load_dotenv()`，测试中需用 `patch.dict(os.environ, {...})` 覆盖环境变量

## 项目架构

`control_window.py` 是主协调器，所有模块在根目录扁平放置（非 package）：

```
main.py → ControlWindow
  ├── config.py — 环境变量加载与 Config 数据类
  ├── selector.py — 全屏透明遮罩拖拽选区（SelectionOverlay）
  ├── border_window.py — 选区绿色边框（WindowTransparentForInput 鼠标穿透）
  ├── capture.py — mss 截图 + JPEG 转换（capture_region → convert_to_jpeg）
  ├── stability.py — MSE 滑动窗口检测画面稳定性 + 内容变化检测
  ├── translator.py — OpenAI 兼容 API 翻译（translate_image 返回 TranslationResult）
  └── result_window.py — 置顶无边框翻译结果窗口（closeEvent 忽略关闭，只隐藏）
```

## 核心流程

1. 用户框选区域 → `SelectionOverlay` 返回全局坐标
2. 点击"开始" → `QTimer` 按 `STABILITY_POLL_INTERVAL`（默认 200ms）轮询
3. 每次轮询：截图 → 稳定性检测（MSE 滑动窗口）→ 内容变化检测（vs 参考画面）→ 间隔约束 → 翻译
4. 翻译在 `TranslationWorker`（`QThread`）后台执行，协作式取消（`_cancelled` 标志）
5. `OpenAI` 客户端由 `ControlWindow` 复用，仅 `base_url` 变化时重建

## 测试注意事项

- 测试使用 `unittest.mock` 的 `patch`/`MagicMock`，无 conftest.py
- GUI 相关测试（`test_control_window.py`、`test_result_window.py`、`test_selector.py`）目前主要测试逻辑而非实际控件，大量使用 `MagicMock` 模拟对象
- 稳定性测试（`test_stability.py`）通过 `_make_png()` 辅助函数生成真实 PNG bytes
- `config.py` 测试必须用 `patch.dict(os.environ)` 覆盖环境变量，因为 `load_dotenv()` 在导入时执行

## 关键细节

- **DPI 处理**：`_on_poll_tick` 中通过 `QScreen.devicePixelRatio()` 将逻辑像素转为物理像素
- **语言映射**：UI 显示中文名（"日语"），API 用英文名（"Japanese"），映射表 `LANG_DISPLAY_TO_ENGLISH`
- **ResultWindow**：`closeEvent` 调用 `event.ignore()` + `self.hide()`，窗口不销毁只隐藏
- **推理深度**：`reasoning_effort` 仅在非 None 时传给 API，None 表示使用模型默认行为
- **截图管线**：`capture_region` 返回 PNG bytes → `convert_to_jpeg` 转为 JPEG 再发给 API

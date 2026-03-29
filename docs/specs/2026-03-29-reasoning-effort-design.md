# 推理深度控制设计

**日期**: 2026-03-29
**状态**: 已批准

## 概述

在 Screen Translator 的 UI 中新增推理深度（reasoning_effort）下拉框，允许用户控制模型是否进行推理以及推理的深度。支持 OpenAI o1/o3 系列模型的 `reasoning_effort` 参数。

## 需求

- 用户可在 UI 上选择推理深度：默认 / 关闭 / 低 / 中 / 高
- "默认"表示不传 `reasoning_effort` 参数（使用模型默认行为）
- 其他选项分别对应 `none` / `low` / `medium` / `high`
- 运行/暂停时该控件应被禁用

## 设计

### 1. UI 层 — `control_window.py`

在模型输入框下方新增一行布局：

- `QLabel("推理深度:")`
- `QComboBox`，选项及对应值：

| 显示文本 | 内部值 | API 行为 |
|---------|--------|---------|
| 默认 | `None` | 不传 `reasoning_effort` |
| 关闭 | `"none"` | `reasoning_effort="none"` |
| 低 | `"low"` | `reasoning_effort="low"` |
| 中 | `"medium"` | `reasoning_effort="medium"` |
| 高 | `"high"` | `reasoning_effort="high"` |

默认选中"默认"。运行/暂停时禁用，与模型输入框行为一致。

### 2. 翻译层 — `translator.py`

`translate_image()` 新增可选参数：

```python
def translate_image(
    ...
    reasoning_effort: str | None = None,
) -> str:
```

使用 `**kwargs` 动态构建参数，仅当 `reasoning_effort` 不为 `None` 时传入。

### 3. Worker 传递 — `TranslationWorker`

- 构造函数新增 `reasoning_effort: str | None` 参数
- `run()` 方法将其传递给 `translate_image()`
- `_execute_translation()` 中创建 Worker 时从下拉框读取当前值

### 4. 配置层 — `config.py`

新增环境变量 `REASONING_EFFORT`，默认值为空（对应"默认"行为）。UI 初始化时从 Config 读取默认值。

### 5. 测试 — `tests/test_translator.py`

新增两个测试：
- `test_translate_image_with_reasoning_effort`：验证传值时 API 调用包含该参数
- `test_translate_image_without_reasoning_effort`：验证 `None` 时不传该参数

## 涉及文件

| 文件 | 变更类型 |
|------|---------|
| `config.py` | 新增 `reasoning_effort` 配置项 |
| `control_window.py` | 新增 UI 控件 + Worker 参数传递 |
| `translator.py` | 新增 `reasoning_effort` 参数 |
| `.env.example` | 新增 `REASONING_EFFORT` 说明 |
| `tests/test_translator.py` | 新增 2 个测试用例 |

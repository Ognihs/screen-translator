# 内容变化检测设计

**日期**: 2026-04-01
**状态**: 已批准

## 概述

在现有截图稳定性检测的基础上，增加内容变化检测机制：只有当前画面与上次翻译时的画面相比发生了显著变化时，才将截图发送给 API 进行翻译。通过比较当前帧与参考画面（上次翻译时的截图）的 RMSE 百分比，判断内容是否发生了足够大的变化。

## 动机

现有的稳定性检测（`StabilityChecker`）只比较**相邻帧**的 MSE，判断画面是否在短时间窗口内稳定。但对于**画面一直不变**的场景（如静态文本），稳定性窗口会在 ~1.2 秒后填满，之后每隔 `DEFAULT_INTERVAL` 仍然会重复翻译完全相同的内容，浪费 API 调用。

**问题示例**（默认配置：轮询 200ms，窗口 5，间隔 10s）：

```
T=0.0s   翻译完成 → reset() 清空窗口
T=0.2s   轮询：存储图片（无历史）
T=0.4s   轮询：MSE=0，窗口=[0]
T=0.6s   轮询：MSE=0，窗口=[0,0]
T=0.8s   轮询：MSE=0，窗口=[0,0,0]
T=1.0s   轮询：MSE=0，窗口=[0,0,0,0]
T=1.2s   轮询：MSE=0，窗口=[0,0,0,0,0] → 稳定！但间隔不足
...
T=10.0s  间隔满足 → 再次翻译（完全相同的内容！）
```

## 配置项

在 `.env` 文件和 `Config` 类中新增以下配置项：

| 环境变量 | 含义 | 默认值 | 范围 |
|---|---|---|---|
| `STABILITY_CHANGE_THRESHOLD` | 内容变化百分比阈值（RMSE%） | `1.0` | 0.0-100.0 |

已有配置项保持不变：
- `STABILITY_POLL_INTERVAL`（稳定性轮询间隔，默认 200ms）
- `STABILITY_WINDOW_SIZE`（滑动窗口大小，默认 5）
- `STABILITY_MSE_THRESHOLD`（MSE 阈值，默认 50.0）
- `DEFAULT_INTERVAL`（翻译最小间隔）

### RMSE 百分比计算

```
RMSE% = √MSE / 255 × 100
```

- MSE（均方误差）范围：0 ~ 65025（255²）
- RMSE% 范围：0% ~ 100%
- 含义：平均每个像素通道的偏差占最大可能偏差（255）的百分比
- 阈值 1.0% 表示平均像素通道偏差约 2.55 以内视为"未变化"

## 架构

### 方案选择

选择扩展 `StabilityChecker` 方案（方案 A），理由：
- 图像解码、MSE 计算的基础设施已在 `StabilityChecker` 中，零代码重复
- `ControlWindow` 改动最小（只增加一个方法调用和一个字段）
- 稳定性检测和内容变化检测都是"图像比较"职责，内聚性合理

### `stability.py` 改动

#### 新增属性

- `_reference_image: np.ndarray | None` — 上次翻译时的画面快照（初始为 None）
- `_change_threshold: float` — 变化百分比阈值（0.0~100.0）

#### 修改 `__init__()` 签名

```python
def __init__(self, window_size: int, mse_threshold: float, change_threshold: float):
    # ... 现有初始化 ...
    self._change_threshold = change_threshold
    self._reference_image: np.ndarray | None = None
```

#### 新增 `content_changed()` 方法

```python
def content_changed(self, image_data: bytes) -> bool:
    """判断当前画面与参考画面相比是否发生了显著变化。

    首次调用时（无参考画面）返回 True，确保第一次翻译能触发。
    后续调用时计算 RMSE%，大于阈值返回 True。

    Args:
        image_data: PNG 格式的截图 bytes

    Returns:
        True 表示内容发生了显著变化，False 表示与参考画面相同
    """
    image = self._decode_image(image_data)
    if self._reference_image is None:
        return True
    mse = self._compute_mse(self._reference_image, image)
    rmse_percent = (mse ** 0.5) / 255.0 * 100.0
    return rmse_percent > self._change_threshold
```

#### 新增 `update_reference()` 方法

```python
def update_reference(self, image_data: bytes) -> None:
    """将当前画面保存为参考画面（翻译完成后调用）。

    Args:
        image_data: PNG 格式的截图 bytes
    """
    self._reference_image = self._decode_image(image_data)
```

#### 修改 `reset()` 方法

保持现有行为（清空 `_mse_history` 和 `_last_image`），**不清除** `_reference_image`。

`_reference_image` 是翻译后的长期参考基准，不是短时窗口状态，不应随 `reset()` 清除。

### `config.py` 改动

在 `Config.__init__()` 中新增：

```python
change_threshold_str = os.getenv("STABILITY_CHANGE_THRESHOLD", "") or "1.0"
try:
    self.stability_change_threshold: float = max(0.0, min(100.0, float(change_threshold_str)))
except ValueError:
    self.stability_change_threshold: float = 1.0
```

### `control_window.py` 改动

#### 构造函数

```python
self._stability_checker = StabilityChecker(
    window_size=self._config.stability_window_size,
    mse_threshold=self._config.stability_mse_threshold,
    change_threshold=self._config.stability_change_threshold,  # 新增
)
self._last_translate_image_data: bytes | None = None  # 新增：保存翻译时的截图
```

#### `_on_poll_tick()` 方法

在稳定性检查通过后、间隔检查之前，插入内容变化检测：

```python
if not is_stable:
    return

# 新增：内容变化检测
if not self._stability_checker.content_changed(screenshot_data):
    return  # 画面与上次翻译时相同，跳过

# 间隔检查（不变）
```

#### `_do_translate()` 方法

保存翻译时使用的截图数据：

```python
def _do_translate(self, image_data: bytes):
    self._last_translate_image_data = image_data  # 新增
    # ... 其余不变 ...
```

#### `_on_translation_completed()` 回调

翻译完成后更新参考画面：

```python
def _on_translation_completed(self, result: str):
    if self._last_translate_image_data is not None:
        self._stability_checker.update_reference(self._last_translate_image_data)
    self._last_translation_time = time.monotonic()
    self._stability_checker.reset()
    # ... 其余不变 ...
```

#### `_on_translation_failed()` 回调

翻译失败时也更新参考画面（避免对同一错误画面反复翻译）：

```python
def _on_translation_failed(self, error_msg: str):
    if self._last_translate_image_data is not None:
        self._stability_checker.update_reference(self._last_translate_image_data)
    self._last_translation_time = time.monotonic()
    self._stability_checker.reset()
    # ... 其余不变 ...
```

### 完整流程

```
轮询定时器(200ms) → 截图 → 稳定性检测(相邻帧MSE)
    → 不稳定? → 跳过
    → 稳定 → 内容变化检测(与参考画面RMSE%)
        → 未变化? → 跳过（节省API调用）
        → 已变化 → 间隔检查(≥DEFAULT_INTERVAL?)
            → 不满足 → 跳过
            → 满足 → 翻译 → 更新参考画面 → reset()
```

### 修改文件清单

| 文件 | 改动 |
|---|---|
| `stability.py` | 新增 `_reference_image`、`_change_threshold` 属性；新增 `content_changed()`、`update_reference()` 方法；修改 `__init__()` 签名 |
| `config.py` | 新增 `stability_change_threshold` 属性 |
| `.env.example` | 新增 `STABILITY_CHANGE_THRESHOLD` 配置项及注释 |
| `control_window.py` | 新增 `_last_translate_image_data` 字段；在 `_on_poll_tick()` 中增加变化检测；在翻译回调中更新参考画面 |
| `tests/test_stability.py` | 新增内容变化检测相关测试 |
| `tests/test_config.py` | 测试新增配置项的默认值和范围约束 |

## 错误处理与边界情况

| 场景 | 处理方式 |
|---|---|
| `content_changed()` 解码失败 | 与现有 `check()` 一致，外层 `_on_poll_tick()` 的 try/except 跳过 |
| 首次翻译（无参考画面） | `content_changed()` 返回 True，确保第一次翻译能触发 |
| 翻译失败 | 也更新参考画面，避免对同一错误画面反复翻译 |
| 暂停/恢复 | 不影响参考画面（`reset()` 不清除 `_reference_image`） |
| 停止 | 不需要特殊处理参考画面 |
| `_last_translate_image_data` 为 None | 在回调中做 None 检查，跳过参考画面更新 |

## 测试计划

### `tests/test_stability.py` 新增测试

- `test_content_changed_returns_true_when_no_reference` — 首次调用（无参考画面）返回 True
- `test_content_changed_returns_false_when_identical` — 相同图片返回 False
- `test_content_changed_returns_true_when_above_threshold` — 差异超过阈值返回 True
- `test_content_changed_returns_false_when_below_threshold` — 差异低于阈值返回 False
- `test_update_reference_updates_reference_image` — 更新参考画面后，相同图片不再变化
- `test_reset_does_not_clear_reference` — `reset()` 后参考画面保留
- `test_change_threshold_boundary` — RMSE% 恰好等于阈值时返回 False（`>` 而非 `>=`）

### `tests/test_config.py` 新增测试

- 测试 `stability_change_threshold` 默认值为 1.0
- 测试范围约束（0.0~100.0）
- 测试无效值回退到默认值

# 截图稳定性检测设计

**日期**: 2026-03-31
**状态**: 已批准

## 概述

在截图翻译流程中增加稳定性检测机制：只有当选区范围内的画面内容相对稳定时，才将截图发送给 API 进行翻译。通过独立快速轮询定时器持续截图，使用 MSE（均方误差）比较相邻帧，配合滑动窗口判断画面是否稳定。

## 动机

当前应用按固定间隔（`DEFAULT_INTERVAL`）触发截图和翻译，无论画面是否发生变化。这导致：
- 画面未变化时重复发送相同内容，浪费 API 调用
- 画面正在变化（如动画、滚动）时翻译结果不准确
- 无法在画面稳定后立即响应，只能等下一个定时器周期

## 配置项

在 `.env` 文件和 `Config` 类中新增以下配置项：

| 环境变量 | 含义 | 默认值 | 范围 |
|---|---|---|---|
| `STABILITY_POLL_INTERVAL` | 稳定性轮询间隔（毫秒） | `200` | 50-2000 |
| `STABILITY_WINDOW_SIZE` | 滑动窗口大小（连续稳定次数） | `5` | 2-20 |
| `STABILITY_MSE_THRESHOLD` | MSE 阈值，低于此值视为"稳定" | `50.0` | 0.0-10000.0 |

已有配置项 `DEFAULT_INTERVAL`（截图间隔）继续生效，作为两次翻译之间的最小间隔约束。

## 架构

### 方案选择

选择独立 `stability.py` 模块方案（方案 A），理由：
- 关注点分离，MSE/滑动窗口逻辑可独立单元测试
- `ControlWindow` 已有 474 行，避免继续膨胀
- 截图和 MSE 计算都是毫秒级操作，无需后台线程

### 新增文件

#### `stability.py`

```python
class StabilityChecker:
    """截图稳定性检测器"""

    def __init__(self, window_size: int, mse_threshold: float):
        self._window_size = window_size
        self._mse_threshold = mse_threshold
        self._mse_history: collections.deque[float]  # maxlen=window_size
        self._last_image: numpy.ndarray | None = None

    def reset(self):
        """清空窗口和缓存，翻译触发后调用"""

    def check(self, image_data: bytes) -> bool:
        """传入当前截图（PNG bytes），返回画面是否稳定

        1. 将 image_data 解码为 numpy 数组（RGB）
        2. 与 _last_image 计算逐像素 MSE
        3. 将 MSE 追加到滑动窗口
        4. 判断窗口内是否全部低于阈值
        5. 更新 _last_image
        6. 返回是否稳定
        """
```

**MSE 计算**：
- 使用 PIL 解码 + `numpy.array()` 转数组
- 不缩放，直接在原始分辨率上计算
- MSE 公式：`np.mean((a.astype(float) - b.astype(float)) ** 2)`
- MSE 数值范围：0（完全一致）~ 65025（完全不同，255²）

### 滑动窗口机制

每次轮询截图一次，与上一次截图计算 MSE，得到一个 MSE 值。维护一个长度为 `STABILITY_WINDOW_SIZE` 的滑动窗口，存储最近的 MSE 值。

**示例**（`STABILITY_WINDOW_SIZE=5`，`STABILITY_MSE_THRESHOLD=50`）：

```
时刻    MSE值    滑动窗口（最近5个）         全部<阈值？
T1      120      [120]                      ✗
T2      80       [120, 80]                  ✗
T3      30       [120, 80, 30]              ✗
T4      25       [120, 80, 30, 25]          ✗
T5      20       [120, 80, 30, 25, 20]      ✗（120>50）
T6      15       [80, 30, 25, 20, 15]       ✗（80>50）
T7      10       [30, 25, 20, 15, 10]       ✓ → 触发翻译！
```

**关键点**：
- 每次轮询只比较**相邻两次**截图的 MSE
- 窗口滑动时丢弃最老的值，加入最新的值
- 当窗口内**所有** MSE 值都低于阈值时，认为画面稳定
- 一旦触发翻译，窗口清空重新开始积累

### ControlWindow 集成

#### 流程变化

```
旧流程：  定时器(秒级) → 截图 → 翻译
新流程：  轮询定时器(毫秒级) → 截图 → MSE比较 → 稳定? → 距上次翻译≥间隔? → 翻译
```

#### 具体改动

1. **替换定时器**：原来的 `_timer`（间隔 = `DEFAULT_INTERVAL`）改为 `_poll_timer`（间隔 = `STABILITY_POLL_INTERVAL`）
2. **新增状态**：
   - `_last_translation_time: float` — 记录上次翻译完成的时间戳（`time.monotonic()`）
   - `_stability_checker: StabilityChecker` — 稳定性检测器实例
3. **新增 `_on_poll_tick()`**（替代 `_on_timer_tick()`）：
   - 截图 → `stability_checker.check()`
   - 如果稳定且距上次翻译 ≥ `DEFAULT_INTERVAL` → 执行翻译，`reset()` 稳定性窗口
   - 如果正在翻译中（`_is_translating`）→ 跳过
4. **翻译完成回调**：
   - 记录 `_last_translation_time = time.monotonic()`
   - 调用 `stability_checker.reset()`

#### 定时器行为对比

| | 旧 | 新 |
|---|---|---|
| 定时器间隔 | `DEFAULT_INTERVAL`（秒级） | `STABILITY_POLL_INTERVAL`（毫秒级） |
| 触发条件 | 固定间隔 | 画面稳定 + 间隔约束 |
| 翻译后 | 等下次定时器触发 | 清空窗口，重新积累稳定性 |

### 修改文件清单

| 文件 | 改动 |
|---|---|
| `stability.py` | **新增** — `StabilityChecker` 类 |
| `config.py` | 新增 `stability_poll_interval`、`stability_window_size`、`stability_mse_threshold` 属性 |
| `.env.example` | 新增三个配置项及注释 |
| `control_window.py` | 替换定时器为轮询定时器，集成 `StabilityChecker`，修改翻译触发逻辑 |
| `pyproject.toml` | 无需修改（`numpy` 已在依赖中） |

## 错误处理与边界情况

| 场景 | 处理方式 |
|---|---|
| 截图失败（`capture_region` 抛异常） | 跳过本次轮询，不更新窗口，不中断轮询定时器 |
| MSE 计算失败（图片解码异常） | 同上，跳过本次 |
| 翻译正在进行中（`_is_translating=True`） | 跳过本次轮询，即使画面稳定也不重复触发 |
| 首次截图（无 `_last_image`） | 只存储图片，不计算 MSE，窗口为空不算稳定 |
| 暂停 | 停止轮询定时器，清空稳定性窗口，取消当前翻译 |
| 恢复 | 重启轮询定时器，窗口从空开始积累 |
| 停止 | 同暂停，额外清除选区和结果窗口 |

## 依赖

项目已有 `Pillow`，`numpy`，无需额外引入。

## 测试计划

- `tests/test_stability.py`：
  - 测试 `StabilityChecker.check()` 在不同 MSE 值下的稳定性判断
  - 测试滑动窗口的滑动和清空行为
  - 测试 `reset()` 方法
  - 测试首次截图（无历史图片）的行为
  - 测试边界值（MSE 恰好等于阈值）
- 更新 `tests/test_config.py`：测试新增配置项的默认值和范围约束

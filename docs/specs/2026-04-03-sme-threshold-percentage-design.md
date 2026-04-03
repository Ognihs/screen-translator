# 稳定性阈值百分比化设计

**日期**: 2026-04-03
**状态**: 已批准

## 概述

将画面稳定性检测的 MSE 阈值从原始 MSE 数值改为 RMSE% 百分比表示，与已有的 `STABILITY_CHANGE_THRESHOLD`（内容变化阈值）保持度量一致，提升配置的直观性和可理解性。

## 动机

当前 `STABILITY_MSE_THRESHOLD` 使用原始 MSE 值（范围 0.0-10000.0），用户难以直觉理解"50.0"代表什么程度的画面差异。项目中 `STABILITY_CHANGE_THRESHOLD` 已经使用 RMSE% 百分比（0.0-100.0），两者使用不同度量体系增加了认知负担。

## 方案选择

### 候选方案

| 方案 | 公式 | 默认值映射 | 优劣 |
|------|------|-----------|------|
| A. RMSE% | `sqrt(MSE)/255 × 100` | MSE=50 → 2.78% | ✅ 与 change_threshold 一致，物理含义清晰 |
| B. MSE/max_MSE% | `MSE/65025 × 100` | MSE=50 → 0.077% | ❌ 实用值集中在 0-1%，范围浪费 |
| C. MSE/1000 简单映射 | `百分比 × 10 = MSE` | MSE=50 → 5.0% | ❌ 无物理含义 |
| D. MAE% | `mean(\|a-b\|)/255 × 100` | 需改核心计算 | ❌ 改动范围大 |

### 选择方案 A（RMSE%）

理由：
1. 项目内一致性：`change_threshold` 已使用 RMSE%，两个阈值用同一套度量
2. 物理含义清晰：百分比直接对应"平均像素偏差占最大色阶的比例"
3. 改动最小：只需在 Config 和 StabilityChecker 中加一层转换

## 设计详情

### 转换公式

用户配置 RMSE% 百分比 → 内部转换为 MSE 阈值：

```
MSE = (threshold / 100 × 255)² = (threshold × 2.55)²
```

| RMSE% | MSE |
|-------|-----|
| 1.0% | 650.25 |
| 3.0% | 58.52 |
| 5.0% | 162.56 |
| 10.0% | 650.25 |

### 配置层变更（config.py）

环境变量重命名：`STABILITY_MSE_THRESHOLD` → `STABILITY_THRESHOLD`

| 变更项 | 旧值 | 新值 |
|--------|------|------|
| 环境变量名 | `STABILITY_MSE_THRESHOLD` | `STABILITY_THRESHOLD` |
| Config 属性名 | `stability_mse_threshold` | `stability_threshold` |
| 值语义 | 原始 MSE | RMSE% |
| 默认值 | 50.0 | 3.0 |
| 范围 | 0.0-10000.0 | 0.0-100.0 |

```python
# config.py
threshold_str = os.getenv("STABILITY_THRESHOLD", "") or "3.0"
try:
    self.stability_threshold: float = max(0.0, min(100.0, float(threshold_str)))
except ValueError:
    self.stability_threshold: float = 3.0
```

### StabilityChecker 变更（stability.py）

构造函数参数从 `mse_threshold` 改为 `threshold`，接收 RMSE% 百分比值，内部转换为 MSE 阈值存储。

```python
# 旧
def __init__(self, window_size: int, mse_threshold: float, change_threshold: float = 0.0):
    self._mse_threshold = mse_threshold

# 新
def __init__(self, window_size: int, threshold: float, change_threshold: float = 0.0):
    self._mse_threshold = (threshold / 100.0 * 255.0) ** 2
```

**不变的部分**：
- `_mse_threshold` 内部属性名不变，仍存储 MSE 值
- `check()` 方法的比较逻辑 `mse_val <= self._mse_threshold` 不变
- `_compute_mse()` 静态方法不变
- `content_changed()` 和 `update_reference()` 不变

**设计决策**：选择在构造时反向投影（RMSE% → MSE），而非在 `check()` 中正向计算（MSE → RMSE%），因为 `check()` 在滑动窗口内对每个元素做比较，避免每次循环的开方运算。

### 调用方变更（control_window.py）

```python
# 旧
self._stability_checker = StabilityChecker(
    window_size=self._config.stability_window_size,
    mse_threshold=self._config.stability_mse_threshold,
    change_threshold=self._config.stability_change_threshold,
)

# 新
self._stability_checker = StabilityChecker(
    window_size=self._config.stability_window_size,
    threshold=self._config.stability_threshold,
    change_threshold=self._config.stability_change_threshold,
)
```

### 配置文件变更（.env.example）

```bash
# 旧
# 稳定性 MSE 阈值（低于此值视为稳定, 默认 50.0, 范围 0.0-10000.0）
STABILITY_MSE_THRESHOLD=50.0

# 新
# 稳定性阈值（RMSE% 低于此值视为稳定, 默认 3.0, 范围 0.0-100.0）
STABILITY_THRESHOLD=3.0
```

### 测试变更

**tests/test_config.py**：
- `test_stability_mse_threshold_default` → `test_stability_threshold_default`，断言 3.0
- `test_stability_mse_threshold_custom` → `test_stability_threshold_custom`，范围改为 0.0-100.0
- `test_stability_mse_threshold_invalid_fallback` → `test_stability_threshold_invalid_fallback`，断言 3.0

**tests/test_stability.py**：
- 所有 `mse_threshold=50.0` 改为 `threshold=3.0`（新默认值）
- 测试预期值根据新阈值（MSE≈58.5）相应调整

## 影响范围

| 文件 | 变更类型 |
|------|----------|
| `config.py` | 重命名属性，更改范围和默认值 |
| `stability.py` | 构造函数参数重命名，增加转换逻辑 |
| `control_window.py` | 更新调用参数名 |
| `.env.example` | 更新环境变量名和注释 |
| `tests/test_config.py` | 更新测试用例名和断言值 |
| `tests/test_stability.py` | 更新参数名和预期值 |

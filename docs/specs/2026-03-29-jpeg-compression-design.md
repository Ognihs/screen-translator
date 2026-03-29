# 截图 JPEG 压缩设计

**日期**: 2026-03-29
**状态**: 已批准

## 背景

当前截图功能使用 `mss` 库截取屏幕区域，输出原始 PNG 格式数据，直接 base64 编码后发送给 LLM 多模态 API。PNG 是无损格式，文件体积较大，导致：

- API 请求 payload 过大，传输耗时增加
- 部分 API 对图片大小有限制
- 浪费 token 额度

## 目标

在截图发送给 API 之前，将其转换为 JPEG 格式并降低质量，以减小传输数据量。JPEG quality 作为可配置项，通过 `.env` 文件设置。

## 方案选择

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| A: 修改 `capture_region()` 输出 JPEG | 直接改截图函数输出格式 | 改动最少 | 破坏现有契约和测试 |
| **B: 新增 `convert_to_jpeg()` 函数** | 在 `capture.py` 新增转换函数，`control_window` 中调用 | 不破坏现有契约；职责清晰；可独立测试 | 多一步调用 |
| C: 在 `translator.py` 中转换 | 发送 API 前在翻译层转换 | 调用方无感 | 违反单一职责；quality 配置需穿透到 translator |

**选定方案 B**。

## 设计详情

### 1. 配置层

**文件**: `config.py`

在 `Config` 类中新增 `jpeg_quality` 属性：

```python
quality_str = os.getenv("JPEG_QUALITY", "") or "75"
self.jpeg_quality: int = max(1, min(95, int(quality_str)))
```

- 从环境变量 `JPEG_QUALITY` 读取，默认值 `75`
- 范围限制在 `1-95`（JPEG quality 有效范围）
- 无效值会抛出 `ValueError`（与现有 `DEFAULT_INTERVAL` 行为一致）

**文件**: `.env.example`

新增：
```
JPEG_QUALITY=75
```

### 2. 图像转换函数

**文件**: `capture.py`

新增 `convert_to_jpeg()` 函数：

```python
from io import BytesIO
from PIL import Image

def convert_to_jpeg(png_data: bytes, quality: int = 75) -> bytes:
    """将 PNG 图像数据转换为 JPEG 格式并压缩。

    Args:
        png_data: PNG 格式的图像 bytes
        quality: JPEG 压缩质量 (1-95)

    Returns:
        JPEG 格式的 bytes 数据
    """
    image = Image.open(BytesIO(png_data))
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGB")
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return buffer.getvalue()
```

关键点：
- 使用项目已依赖的 Pillow 库（`pillow>=12.1.1`），无需新增依赖
- 处理 RGBA/LA/P 模式（带 alpha 通道），转为 RGB 以兼容 JPEG
- `quality` 参数由调用方传入，保持纯函数，易于测试
- `capture_region()` 函数签名和行为不变，现有测试不受影响

### 3. 调用链改动

**文件**: `control_window.py`

在 `_execute_translation()` 方法中，截图后增加转换步骤：

```python
from capture import capture_region, convert_to_jpeg

image_data = capture_region(physical_x, physical_y, physical_width, physical_height)
image_data = convert_to_jpeg(image_data, quality=self._config.jpeg_quality)
```

**文件**: `translator.py`

将 MIME 类型从 `image/png` 改为 `image/jpeg`：

```python
"url": f"data:image/jpeg;base64,{b64_image}"
```

同时更新 `translate_image()` 函数文档字符串中的参数说明（`PNG 格式的截图 bytes` → `图像截图 bytes`）。

### 4. 测试

**文件**: `tests/test_capture.py`

新增测试用例：

- `test_convert_to_jpeg_returns_jpeg_bytes` — 验证返回 JPEG 格式数据（检查 JPEG magic bytes `\xff\xd8\xff`）
- `test_convert_to_jpeg_respects_quality` — 验证不同 quality 参数产生不同大小的输出
- `test_convert_to_jpeg_handles_rgba` — 验证 RGBA 输入能正确转换为 RGB JPEG

现有 `test_capture_region_returns_bytes` 和 `test_capture_region_invalid_size` 不受影响。

## 数据流

```
capture_region()          convert_to_jpeg()           translate_image()
    PNG bytes      →        JPEG bytes        →        base64 JPEG → API
                            (quality from
                             Config.jpeg_quality)
```

## 影响范围

| 文件 | 改动类型 |
|------|----------|
| `config.py` | 新增 `jpeg_quality` 属性 |
| `capture.py` | 新增 `convert_to_jpeg()` 函数 |
| `control_window.py` | 导入并调用 `convert_to_jpeg()` |
| `translator.py` | MIME 类型改为 `image/jpeg`，更新文档 |
| `.env.example` | 新增 `JPEG_QUALITY` |
| `tests/test_capture.py` | 新增 3 个测试用例 |

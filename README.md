# Screen Translator

一个通过截图调用多模态 API 进行屏幕区域文字翻译的 Python 桌面应用。用户通过鼠标框选屏幕区域，应用按设定间隔自动截取该区域并调用 OpenAI 兼容 API 翻译，翻译结果在置顶窗口中实时显示。

## 功能特性

- 🖱️ **鼠标框选** — 全屏透明遮罩，拖拽选取屏幕任意区域
- 🔄 **定时翻译** — 可配置截图间隔（1-300 秒），自动循环截图翻译
- 🌐 **多语言支持** — 支持中文、日语、英语互译
- 🔌 **OpenAI 兼容** — 支持任何 OpenAI 兼容接口（DeepSeek、GLM、Ollama 等）
- 📌 **置顶结果窗口** — 翻译结果始终可见，支持拖动和调整大小
- 🎯 **选区边框** — 绿色边框标记当前选区，鼠标穿透不影响操作
- ⏸️ **暂停/继续** — 随时暂停和恢复翻译循环

## 技术栈

- **Python 3.14**
- **PySide6** — GUI 框架
- **mss** — 屏幕截图
- **openai** — 多模态 API 客户端
- **python-dotenv** — 环境变量管理

## 安装

### 前置要求

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/) 包管理器

### 步骤

1. 克隆仓库：

```bash
git clone <repository-url>
cd screen-translator
```

2. 安装依赖：

```bash
uv sync
```

## 配置

1. 复制环境变量模板：

```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的 API 配置：

```ini
API_KEY=your-api-key-here
BASE_URL=https://api.openai.com/v1
MODEL=gpt-4o
DEFAULT_INTERVAL=10
```

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `API_KEY` | 多模态 API 的密钥 | 无 |
| `BASE_URL` | API 基础地址 | `https://api.openai.com/v1` |
| `MODEL` | 使用的模型名称 | `gpt-4o` |
| `DEFAULT_INTERVAL` | 默认截图间隔（秒） | `10` |

> **注意**：`API_KEY` 为必填项，其他配置项均有默认值。API 地址和模型也可在控制面板中实时修改。

## 使用方法

### 启动应用

```bash
uv run python main.py
```

### 操作流程

1. **选择区域** — 点击「选择区域」按钮，屏幕出现半透明遮罩，拖拽鼠标框选需要翻译的区域，按 ESC 可取消
2. **开始翻译** — 点击「开始」按钮，应用按设定间隔自动截图并翻译
3. **查看结果** — 翻译结果显示在置顶的结果窗口中
4. **暂停/继续** — 点击「暂停」按钮暂停翻译循环，再次点击继续
5. **停止** — 点击「停止」按钮停止翻译并清除选区

### 控制面板

```
┌─────────────────────────────┐
│  Screen Translator          │
├─────────────────────────────┤
│ 源语言: [日语 ▼]            │
│ 目标语言: [中文 ▼]          │
│                             │
│ 截图间隔: [10] 秒           │
│                             │
│ API地址: [________________] │
│ 模型:   [________________]  │
│                             │
│ [选择区域]  [开始] [暂停]   │
│            [停止]           │
│                             │
│ 状态: 就绪                  │
└─────────────────────────────┘
```

## 项目结构

```
screen-translator/
├── main.py              # 应用入口
├── config.py            # 配置管理（.env 加载）
├── selector.py          # 全屏透明遮罩，鼠标拖拽选区
├── capture.py           # 截图引擎（mss 截取指定区域）
├── translator.py        # OpenAI 兼容 API 翻译客户端
├── border_window.py     # 选区边框窗口（置顶、鼠标穿透）
├── result_window.py     # 翻译结果展示窗口（置顶、可拖动）
├── control_window.py    # 主控制面板（协调所有模块）
├── .env.example         # 环境变量模板
├── pyproject.toml       # 项目依赖配置
└── tests/               # 单元测试
    ├── test_config.py   # 配置模块测试
    ├── test_capture.py  # 截图引擎测试
    └── test_translator.py # 翻译客户端测试
```

## 架构概览

```
main.py → ControlWindow（主协调者）
           ├── Config（配置管理）
           ├── SelectionOverlay（选区遮罩）
           ├── BorderWindow（选区边框）
           ├── QTimer → capture_region() → translate_image()
           └── ResultWindow（翻译结果显示）
```

核心数据流：

```
用户点击「选区」 → selector.py 全屏遮罩 → 用户拖拽选区 → 返回坐标
                                                            ↓
用户点击「开始」 → QTimer 启动 → capture.py 截取选区 → translator.py 调用 API
                                                            ↓
                                                result_window.py 显示翻译结果
```

## 开发

### 运行测试

```bash
uv run pytest tests/ -v
```

### 运行单个测试文件

```bash
uv run pytest tests/test_config.py -v
uv run pytest tests/test_capture.py -v
uv run pytest tests/test_translator.py -v
```

## 支持的 API 服务

任何兼容 OpenAI Chat Completions 接口的多模态服务均可使用，包括但不限于：

- OpenAI（GPT-4o 等）
- DeepSeek
- GLM（智谱）
- Ollama（本地模型）
- 其他 OpenAI 兼容服务

只需在 `.env` 或控制面板中配置对应的 `BASE_URL` 和 `MODEL` 即可。

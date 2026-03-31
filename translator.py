# translator.py
import base64
from dataclasses import dataclass

from openai import APITimeoutError, APIStatusError, OpenAI


@dataclass
class TranslationResult:
    """翻译结果

    Attributes:
        text: 翻译文本或错误信息
        is_error: 是否为错误结果
    """

    text: str
    is_error: bool = False


def translate_image(
    image_data: bytes,
    source_lang: str,
    target_lang: str,
    api_key: str,
    base_url: str,
    model: str,
    reasoning_effort: str | None = None,
    client: OpenAI | None = None,
) -> TranslationResult:
    """将截图发送给多模态 API 进行翻译。

    Args:
        image_data: JPEG 格式的截图 bytes
        source_lang: 源语言（中文/日语/英语）
        target_lang: 目标语言（中文/日语/英语）
        api_key: API 密钥
        base_url: API 基础 URL
        model: 模型名称
        reasoning_effort: 推理深度（none/low/medium/high），None 表示使用模型默认行为
        client: 可选的 OpenAI 客户端实例，传入时复用连接池，忽略 api_key/base_url

    Returns:
        TranslationResult 包含翻译文本和错误标志
    """
    try:
        if client is None:
            client = OpenAI(api_key=api_key, base_url=base_url)

        b64_image = base64.b64encode(image_data).decode("utf-8")

        prompt = f"请将图片中的{source_lang}文本翻译为{target_lang}，仅输出翻译结果，不要添加解释"

        kwargs = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}"
                            },
                        },
                    ],
                }
            ],
            "timeout": 30.0,
        }
        if reasoning_effort is not None:
            kwargs["reasoning_effort"] = reasoning_effort

        response = client.chat.completions.create(**kwargs)

        if not response.choices:
            return TranslationResult(text="错误：API 未返回有效响应", is_error=True)

        content = response.choices[0].message.content
        if not content or not content.strip():
            return TranslationResult(text="（未检测到文本）")
        return TranslationResult(text=content.strip())

    except APITimeoutError:
        return TranslationResult(
            text="错误：翻译超时，请检查网络连接", is_error=True
        )
    except APIStatusError as e:
        return TranslationResult(
            text=f"错误：API 返回错误（{e.status_code}），请检查配置",
            is_error=True,
        )
    except Exception as e:
        return TranslationResult(
            text=f"错误：{type(e).__name__} — {e}", is_error=True
        )

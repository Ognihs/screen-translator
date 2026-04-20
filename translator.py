# translator.py
import base64
import logging
from dataclasses import dataclass
from typing import Literal

ReasoningEffort = Literal["none", "low", "medium", "high"]

from openai import APITimeoutError, APIStatusError, OpenAI

logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_TIMEOUT = 30.0  # 默认超时时间（秒）
TRANSLATION_PROMPT_TEMPLATE = """
Translate all visible text in this image from {source_lang} to {target_lang}.

Rules:
- Output ONLY the translated text, nothing else.
- Preserve the original line breaks and spacing.
- Write numbers as digits (e.g., 1.7 not "one point seven").
- Do NOT include any explanation, notes, or the original text.
"""


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
    reasoning_effort: ReasoningEffort | None = None,
    client: OpenAI | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> TranslationResult:
    """将截图发送给多模态 API 进行翻译。

    Args:
        image_data: JPEG 格式的截图 bytes
        source_lang: 源语言的英文名称（English/Japanese/Chinese）
        target_lang: 目标语言的英文名称（English/Japanese/Chinese）
        api_key: API 密钥
        base_url: API 基础 URL
        model: 模型名称
        reasoning_effort: 推理深度（none/low/medium/high），None 表示使用模型默认行为
        client: 可选的 OpenAI 客户端实例，传入时复用连接池，忽略 api_key/base_url
        timeout: 超时时间（秒），默认 30.0

    Returns:
        TranslationResult 包含翻译文本和错误标志
    """
    logger.info(f"翻译请求: {source_lang} -> {target_lang}, 模型: {model}")
    try:
        if client is None:
            logger.debug(f"创建新 API 客户端，base_url: {base_url}")
            client = OpenAI(api_key=api_key, base_url=base_url)

        b64_image = base64.b64encode(image_data).decode("utf-8")

        prompt = TRANSLATION_PROMPT_TEMPLATE.format(
            source_lang=source_lang, target_lang=target_lang
        )

        kwargs = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a precise translator. Translate text found in images as instructed. Output only the translation.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"},
                        },
                    ],
                },
            ],
            "timeout": timeout,
        }
        if reasoning_effort is not None:
            kwargs["reasoning_effort"] = reasoning_effort
            logger.debug(f"设置推理深度: {reasoning_effort}")

        logger.debug("发送翻译请求...")
        response = client.chat.completions.create(**kwargs)
        logger.debug("收到翻译响应")

        if not response.choices:
            logger.error("API 未返回有效响应")
            return TranslationResult(text="错误：API 未返回有效响应", is_error=True)

        content = response.choices[0].message.content
        if not content or not content.strip():
            logger.info("未检测到文本")
            return TranslationResult(text="（未检测到文本）")
        logger.info(f"翻译成功，结果长度: {len(content)} 字符")
        return TranslationResult(text=content.strip())

    except APITimeoutError:
        logger.warning("翻译超时")
        return TranslationResult(text="错误：翻译超时，请检查网络连接", is_error=True)
    except APIStatusError as e:
        logger.error(f"API 错误 ({e.status_code}): {e}")
        return TranslationResult(
            text=f"错误：API 返回错误（{e.status_code}），请检查配置",
            is_error=True,
        )
    except Exception as e:
        logger.error(f"翻译异常: {type(e).__name__} — {e}", exc_info=True)
        return TranslationResult(text=f"错误：{type(e).__name__} — {e}", is_error=True)

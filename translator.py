# translator.py
import base64
import openai
from openai import OpenAI


def translate_image(
    image_data: bytes,
    source_lang: str,
    target_lang: str,
    api_key: str,
    base_url: str,
    model: str,
) -> str:
    """将截图发送给多模态 API 进行翻译。

    Args:
        image_data: JPEG 格式的截图 bytes
        source_lang: 源语言（中文/日语/英语）
        target_lang: 目标语言（中文/日语/英语）
        api_key: API 密钥
        base_url: API 基础 URL
        model: 模型名称

    Returns:
        翻译结果文本，出错时返回错误信息字符串
    """
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)

        b64_image = base64.b64encode(image_data).decode("utf-8")

        prompt = f"请将图片中的{source_lang}文本翻译为{target_lang}，仅输出翻译结果，不要添加解释"

        response = client.chat.completions.create(
            model=model,
            messages=[
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
            timeout=30.0,
        )

        content = response.choices[0].message.content
        if not content or not content.strip():
            return "（未检测到文本）"
        return content.strip()

    except openai.APITimeoutError:
        return "错误：翻译超时，请检查网络连接"
    except openai.APIStatusError as e:
        return f"错误：API 返回错误（{e.status_code}），请检查配置"
    except Exception as e:
        return f"错误：{type(e).__name__} — {e}"
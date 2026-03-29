# tests/test_translator.py
import pytest
from unittest.mock import patch, MagicMock


def test_translate_image_success():
    """测试成功翻译图片"""
    from translator import translate_image

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "你好世界"

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="日语",
            target_lang="中文",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
        )
        assert result == "你好世界"


def test_translate_image_timeout():
    """测试翻译超时"""
    from translator import translate_image
    import openai
    import httpx

    mock_client = MagicMock()
    mock_request = MagicMock(spec=httpx.Request)
    mock_client.chat.completions.create.side_effect = openai.APITimeoutError(mock_request)

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="英语",
            target_lang="中文",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
        )
        assert "超时" in result


def test_translate_image_api_error():
    """测试 API 返回错误"""
    from translator import translate_image
    import openai

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = openai.APIStatusError(
        "rate limited", response=MagicMock(status_code=429), body=None
    )

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="英语",
            target_lang="中文",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
        )
        assert "错误" in result


def test_translate_image_empty_response():
    """测试 API 返回空内容"""
    from translator import translate_image

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = ""

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="英语",
            target_lang="中文",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
        )
        assert "未检测到" in result


def test_translate_image_with_reasoning_effort():
    """测试传入 reasoning_effort 时 API 调用包含该参数"""
    from translator import translate_image

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "你好世界"

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="日语",
            target_lang="中文",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
            reasoning_effort="low",
        )
        assert result == "你好世界"
        # 验证 create 被调用时包含 reasoning_effort 参数
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["reasoning_effort"] == "low"


def test_translate_image_without_reasoning_effort():
    """测试不传 reasoning_effort 时 API 调用不含该参数"""
    from translator import translate_image

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "你好世界"

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="日语",
            target_lang="中文",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
        )
        assert result == "你好世界"
        # 验证 create 被调用时不包含 reasoning_effort 参数
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "reasoning_effort" not in call_kwargs
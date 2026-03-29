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

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = openai.APITimeoutError("timeout")

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
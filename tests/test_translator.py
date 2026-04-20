# tests/test_translator.py
import pytest
from unittest.mock import patch, MagicMock

from translator import translate_image, TranslationResult


def test_translate_image_success():
    """测试成功翻译图片"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "你好世界"

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="Japanese",
            target_lang="Chinese",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
        )
        assert isinstance(result, TranslationResult)
        assert result.text == "你好世界"
        assert not result.is_error


def test_translate_image_timeout():
    """测试翻译超时"""
    import httpx
    from openai import APITimeoutError

    mock_client = MagicMock()
    mock_request = MagicMock(spec=httpx.Request)
    mock_client.chat.completions.create.side_effect = APITimeoutError(mock_request)

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="English",
            target_lang="Chinese",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
        )
        assert isinstance(result, TranslationResult)
        assert result.is_error
        assert "超时" in result.text


def test_translate_image_api_error():
    """测试 API 返回错误"""
    from openai import APIStatusError

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = APIStatusError(
        "rate limited", response=MagicMock(status_code=429), body=None
    )

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="English",
            target_lang="Chinese",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
        )
        assert isinstance(result, TranslationResult)
        assert result.is_error
        assert "错误" in result.text


def test_translate_image_empty_response():
    """测试 API 返回空内容"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = ""

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="English",
            target_lang="Chinese",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
        )
        assert isinstance(result, TranslationResult)
        assert not result.is_error
        assert "未检测到" in result.text


def test_translate_image_whitespace_response():
    """测试 API 返回纯空白内容"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "   \n  "

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="English",
            target_lang="Chinese",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
        )
        assert isinstance(result, TranslationResult)
        assert not result.is_error
        assert "未检测到" in result.text


def test_translate_image_empty_choices():
    """测试 API 返回空 choices 列表"""
    mock_response = MagicMock()
    mock_response.choices = []

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="English",
            target_lang="Chinese",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
        )
        assert isinstance(result, TranslationResult)
        assert result.is_error
        assert "未返回有效响应" in result.text


def test_translate_image_generic_exception():
    """测试通用异常被捕获"""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("unexpected")

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="Japanese",
            target_lang="Chinese",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
        )
        assert isinstance(result, TranslationResult)
        assert result.is_error
        assert "RuntimeError" in result.text
        assert "unexpected" in result.text


def test_translate_image_with_reasoning_effort():
    """测试传入 reasoning_effort 时 API 调用包含该参数"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "你好世界"

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="Japanese",
            target_lang="Chinese",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
            reasoning_effort="low",
        )
        assert result.text == "你好世界"
        # 验证 create 被调用时包含 reasoning_effort 参数
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["reasoning_effort"] == "low"


def test_translate_image_without_reasoning_effort():
    """测试不传 reasoning_effort 时 API 调用不含该参数"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "你好世界"

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("translator.OpenAI", return_value=mock_client):
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="Japanese",
            target_lang="Chinese",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
        )
        assert result.text == "你好世界"
        # 验证 create 被调用时不包含 reasoning_effort 参数
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "reasoning_effort" not in call_kwargs


def test_translate_image_with_client():
    """测试传入 client 时复用客户端而不创建新实例"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "你好世界"

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("translator.OpenAI") as mock_openai_cls:
        result = translate_image(
            image_data=b"fake-png-bytes",
            source_lang="Japanese",
            target_lang="Chinese",
            api_key="test-key",
            base_url="https://api.example.com/v1",
            model="test-model",
            client=mock_client,
        )
        assert result.text == "你好世界"
        # 验证没有创建新的 OpenAI 实例
        mock_openai_cls.assert_not_called()
        # 验证使用了传入的 client
        mock_client.chat.completions.create.assert_called_once()

# tests/test_config.py
import os
import pytest
from unittest.mock import patch


def test_load_config_from_env():
    """测试从环境变量加载配置"""
    env_vars = {
        "API_KEY": "test-key",
        "BASE_URL": "https://api.example.com/v1",
        "MODEL": "test-model",
        "DEFAULT_INTERVAL": "15",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        from config import Config
        cfg = Config()
        assert cfg.api_key == "test-key"
        assert cfg.base_url == "https://api.example.com/v1"
        assert cfg.model == "test-model"
        assert cfg.default_interval == 15


def test_default_values():
    """测试未设置环境变量时的默认值"""
    env_vars = {
        "API_KEY": "",
        "BASE_URL": "",
        "MODEL": "",
        "DEFAULT_INTERVAL": "",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        from config import Config
        cfg = Config()
        assert cfg.api_key == ""
        assert cfg.base_url == "https://api.openai.com/v1"
        assert cfg.model == "gpt-4o"
        assert cfg.default_interval == 10


def test_jpeg_quality_default():
    """测试 jpeg_quality 默认值为 75"""
    with patch.dict(os.environ, {"JPEG_QUALITY": ""}, clear=False):
        from config import Config
        cfg = Config()
        assert cfg.jpeg_quality == 75


def test_jpeg_quality_custom():
    """测试 jpeg_quality 从环境变量读取"""
    with patch.dict(os.environ, {"JPEG_QUALITY": "50"}, clear=False):
        from config import Config
        cfg = Config()
        assert cfg.jpeg_quality == 50


def test_jpeg_quality_clamped():
    """测试 jpeg_quality 被正确 clamp 到 1-95 范围"""
    with patch.dict(os.environ, {"JPEG_QUALITY": "100"}, clear=False):
        from config import Config
        cfg = Config()
        assert cfg.jpeg_quality == 95

    with patch.dict(os.environ, {"JPEG_QUALITY": "0"}, clear=False):
        from config import Config
        cfg = Config()
        assert cfg.jpeg_quality == 1

    with patch.dict(os.environ, {"JPEG_QUALITY": "-5"}, clear=False):
        from config import Config
        cfg = Config()
        assert cfg.jpeg_quality == 1


def test_has_api_key():
    """测试 API Key 是否已配置"""
    with patch.dict(os.environ, {"API_KEY": "test-key"}, clear=False):
        from config import Config
        cfg = Config()
        assert cfg.has_api_key is True

    with patch.dict(os.environ, {"API_KEY": ""}, clear=False):
        from config import Config
        cfg = Config()
        assert cfg.has_api_key is False
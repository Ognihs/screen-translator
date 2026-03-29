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
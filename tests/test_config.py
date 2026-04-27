# tests/test_config.py
import os
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
        assert cfg.default_interval == 15.0

    def test_default_values():
        """测试未设置环境变量时的默认值"""
        env_vars = {
            "API_KEY": "",
            "MODEL": "",
            "DEFAULT_INTERVAL": "",
        }
        env_vars_to_remove = ["BASE_URL"]
        with patch.dict(os.environ, env_vars, clear=False):
            for key in env_vars_to_remove:
                os.environ.pop(key, None)
            from config import Config

            cfg = Config()
            assert cfg.api_key == ""
            assert cfg.base_url == "https://api.openai.com/v1"
        assert cfg.model == "gpt-4o"
        assert cfg.default_interval == 10.0


def test_jpeg_quality_default():
    """测试 jpeg_quality 默认值为 75"""
    with patch.dict(os.environ, {"JPEG_QUALITY": ""}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.jpeg_quality == 75


def test_jpeg_quality_custom():
    """测试 jpeg_quality 从环境变量读取"""
    with patch.dict(os.environ, {"JPEG_QUALITY": "90"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.jpeg_quality == 90


def test_jpeg_quality_invalid_fallback():
    """测试 jpeg_quality 无效输入回退到默认值 75"""
    with patch.dict(os.environ, {"JPEG_QUALITY": "not_a_number"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.jpeg_quality == 75


def test_jpeg_quality_clamped_to_valid_range():
    """测试 jpeg_quality 限制在 1-95 范围内"""
    with patch.dict(os.environ, {"JPEG_QUALITY": "200"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.jpeg_quality == 95

    with patch.dict(os.environ, {"JPEG_QUALITY": "0"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.jpeg_quality == 1


def test_reasoning_effort_default():
    """测试 reasoning_effort 默认值为 None"""
    with patch.dict(os.environ, {"REASONING_EFFORT": ""}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.reasoning_effort is None


def test_reasoning_effort_custom():
    """测试 reasoning_effort 从环境变量读取"""
    with patch.dict(os.environ, {"REASONING_EFFORT": "high"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.reasoning_effort == "high"


def test_has_api_key():
    """测试 has_api_key 属性"""
    with patch.dict(os.environ, {"API_KEY": "  "}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.has_api_key is False

    with patch.dict(os.environ, {"API_KEY": "sk-test"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.has_api_key is True


def test_stability_poll_interval_default():
    """测试 stability_poll_interval 默认值为 200"""
    with patch.dict(os.environ, {"STABILITY_POLL_INTERVAL": ""}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.stability_poll_interval == 200


def test_stability_poll_interval_custom():
    """测试 stability_poll_interval 从环境变量读取"""
    with patch.dict(os.environ, {"STABILITY_POLL_INTERVAL": "500"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.stability_poll_interval == 500


def test_stability_poll_interval_invalid_fallback():
    """测试 stability_poll_interval 非数字输入回退到默认值 200"""
    with patch.dict(os.environ, {"STABILITY_POLL_INTERVAL": "not_a_number"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.stability_poll_interval == 200


def test_stability_window_size_default():
    """测试 stability_window_size 默认值为 5"""
    with patch.dict(os.environ, {"STABILITY_WINDOW_SIZE": ""}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.stability_window_size == 5


def test_stability_window_size_custom():
    """测试 stability_window_size 从环境变量读取"""
    with patch.dict(os.environ, {"STABILITY_WINDOW_SIZE": "10"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.stability_window_size == 10


def test_stability_window_size_invalid_fallback():
    """测试 stability_window_size 非数字输入回退到默认值 5"""
    with patch.dict(os.environ, {"STABILITY_WINDOW_SIZE": "not_a_number"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.stability_window_size == 5


def test_stability_threshold_default():
    """测试 stability_threshold 默认值为 3.0"""
    with patch.dict(os.environ, {"STABILITY_THRESHOLD": ""}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.stability_threshold == 3.0


def test_stability_threshold_custom():
    """测试 stability_threshold 从环境变量读取"""
    with patch.dict(os.environ, {"STABILITY_THRESHOLD": "5.0"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.stability_threshold == 5.0


def test_stability_threshold_invalid_fallback():
    """测试 stability_threshold 非数字输入回退到默认值 3.0"""
    with patch.dict(os.environ, {"STABILITY_THRESHOLD": "not_a_number"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.stability_threshold == 3.0


def test_stability_change_threshold_default():
    """测试 stability_change_threshold 默认值为 1.0"""
    with patch.dict(os.environ, {"STABILITY_CHANGE_THRESHOLD": ""}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.stability_change_threshold == 1.0


def test_stability_change_threshold_custom():
    """测试 stability_change_threshold 从环境变量读取"""
    with patch.dict(os.environ, {"STABILITY_CHANGE_THRESHOLD": "2.5"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.stability_change_threshold == 2.5


def test_stability_change_threshold_invalid_fallback():
    """测试 stability_change_threshold 非数字输入回退到默认值 1.0"""
    with patch.dict(os.environ, {"STABILITY_CHANGE_THRESHOLD": "not_a_number"}, clear=False):
        from config import Config

        cfg = Config()
        assert cfg.stability_change_threshold == 1.0


def test_validate_with_missing_api_key():
    """测试 validate() 方法检测缺失的 API Key"""
    with patch.dict(os.environ, {"API_KEY": ""}, clear=False):
        from config import Config

        cfg = Config()
        errors = cfg.validate()
        assert len(errors) > 0
        assert "API_KEY" in errors[0]


def test_validate_with_valid_config():
    """测试 validate() 方法对有效配置返回空列表"""
    with patch.dict(
        os.environ, {"API_KEY": "test-key", "BASE_URL": "https://api.openai.com/v1", "MODEL": "gpt-4o"}, clear=False
    ):
        from config import Config

        cfg = Config()
        errors = cfg.validate()
        assert len(errors) == 0


def test_validate_with_invalid_base_url():
    """测试 validate() 方法检测无效的 Base URL 格式"""
    with patch.dict(os.environ, {"API_KEY": "test-key", "BASE_URL": "invalid-url", "MODEL": "gpt-4o"}, clear=False):
        from config import Config

        cfg = Config()
        errors = cfg.validate()
        assert len(errors) > 0
        assert "BASE_URL" in errors[0]

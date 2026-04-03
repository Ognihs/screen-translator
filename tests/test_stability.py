# tests/test_stability.py
import io

import numpy as np
import pytest
from PIL import Image


def _make_png(color: tuple = (255, 0, 0), size: tuple = (100, 100)) -> bytes:
    """创建指定颜色和尺寸的 PNG 图片 bytes"""
    img = Image.new("RGB", size, color=color)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def test_check_returns_false_on_first_image():
    """首次截图时没有历史图片，不应判定为稳定"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=3, threshold=3.0)
    result = checker.check(_make_png())
    assert result is False


def test_check_returns_false_when_window_not_full():
    """滑动窗口未填满时不应判定为稳定"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=3, threshold=3.0)
    checker.check(_make_png())  # 首次，存储图片
    result = checker.check(_make_png())  # 窗口只有 1 个 MSE 值
    assert result is False


def test_check_returns_true_when_all_below_threshold():
    """窗口填满且全部 MSE 低于阈值时应判定为稳定"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=3, threshold=3.0)
    checker.check(_make_png((255, 0, 0)))  # 存储首帧
    # 相同图片，MSE=0
    assert checker.check(_make_png((255, 0, 0))) is False  # 窗口: [0]，未满
    assert checker.check(_make_png((255, 0, 0))) is False  # 窗口: [0, 0]，未满
    assert checker.check(_make_png((255, 0, 0))) is True   # 窗口: [0, 0, 0]，满且全<50


def test_check_returns_false_when_any_above_threshold():
    """窗口中有任何一个 MSE 高于阈值时不应判定为稳定"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=3, threshold=3.0)
    checker.check(_make_png((0, 0, 0)))        # 存储首帧
    checker.check(_make_png((0, 0, 0)))         # 窗口: [0]
    checker.check(_make_png((255, 255, 255)))   # 窗口: [0, 高MSE]
    # 窗口未满（只有2个），所以返回 False
    assert checker.check(_make_png((0, 0, 0))) is False  # 窗口: [0, 高MSE, 高MSE]


def test_check_mse_at_exact_threshold():
    """MSE 恰好等于阈值时应判定为稳定（<=）"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=2, threshold=0.0)
    checker.check(_make_png((0, 0, 0)))
    # MSE=0 恰好等于阈值 0.0
    assert checker.check(_make_png((0, 0, 0))) is False  # 窗口未满
    assert checker.check(_make_png((0, 0, 0))) is True   # 窗口满，MSE=0 <= 0.0


def test_reset_clears_state():
    """reset 后应清空窗口和历史图片"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=2, threshold=3.0)
    checker.check(_make_png((255, 0, 0)))
    checker.check(_make_png((255, 0, 0)))
    checker.reset()
    # reset 后等同于首次截图
    result = checker.check(_make_png((255, 0, 0)))
    assert result is False


def test_sliding_window_discards_old_values():
    """滑动窗口应丢弃旧值"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=2, threshold=3.0)
    checker.check(_make_png((0, 0, 0)))         # 存储首帧
    checker.check(_make_png((255, 255, 255)))   # 窗口: [高MSE]
    # 现在连续两张相同图片，MSE=0
    assert checker.check(_make_png((255, 255, 255))) is False  # 窗口: [高MSE, 0]
    # 旧的 高MSE 被滑出，窗口: [0, 0]
    assert checker.check(_make_png((255, 255, 255))) is True


def test_content_changed_first_call_returns_true():
    """首次调用 content_changed() 应返回 True（无参考画面）"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=2, threshold=3.0, change_threshold=1.0)
    result = checker.content_changed(_make_png((0, 0, 0)))
    assert result is True


def test_content_changed_same_image_returns_false():
    """相同图片调用 content_changed() 应返回 False"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=2, threshold=3.0, change_threshold=1.0)
    checker.update_reference(_make_png((0, 0, 0)))
    result = checker.content_changed(_make_png((0, 0, 0)))
    assert result is False


def test_content_changed_exceeds_threshold_returns_true():
    """差异超过阈值应返回 True（纯黑 vs RGB(3,3,3)，RMSE%≈1.176% > 1.0%）"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=2, threshold=3.0, change_threshold=1.0)
    checker.update_reference(_make_png((0, 0, 0)))
    # RGB(3,3,3) vs (0,0,0) MSE = 9, RMSE% = sqrt(9)/255*100 ≈ 1.176%
    result = checker.content_changed(_make_png((3, 3, 3)))
    assert result is True


def test_content_changed_below_threshold_returns_false():
    """差异低于阈值应返回 False（纯黑 vs RGB(2,2,2)，RMSE%≈0.784% < 1.0%）"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=2, threshold=3.0, change_threshold=1.0)
    checker.update_reference(_make_png((0, 0, 0)))
    # RGB(2,2,2) vs (0,0,0) MSE = 4, RMSE% = sqrt(4)/255*100 ≈ 0.784%
    result = checker.content_changed(_make_png((2, 2, 2)))
    assert result is False


def test_content_changed_above_threshold_returns_true():
    """RMSE% 超过阈值应返回 True"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=2, threshold=3.0, change_threshold=1.0)
    checker.update_reference(_make_png((0, 0, 0)))
    # RGB(3,3,3) vs (0,0,0) MSE = 9, RMSE% = sqrt(9)/255*100 ≈ 1.18% > 1.0%
    result = checker.content_changed(_make_png((3, 3, 3)))
    assert result is True


def test_reset_does_not_clear_reference_image():
    """reset() 不应清除参考画面"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=2, threshold=3.0, change_threshold=1.0)
    checker.update_reference(_make_png((0, 0, 0)))
    checker.reset()  # reset 不应清除 _reference_image
    # 相同图片应返回 False（参考画面未被清除）
    result = checker.content_changed(_make_png((0, 0, 0)))
    assert result is False


def test_content_changed_with_zero_threshold_always_true_after_first():
    """阈值为 0 时，任何变化都应返回 True"""
    from stability import StabilityChecker

    checker = StabilityChecker(window_size=2, threshold=3.0, change_threshold=0.0)
    checker.update_reference(_make_png((0, 0, 0)))
    # 任何非零差异都应返回 True
    result = checker.content_changed(_make_png((1, 1, 1)))
    assert result is True
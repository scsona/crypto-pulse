"""Tests for the unicode sparkline renderer."""

from crypto_pulse.sparkline import BLOCKS, sparkline


def test_empty():
    assert sparkline([]) == ""


def test_single_value():
    assert sparkline([5]) == BLOCKS[len(BLOCKS) // 2]


def test_flat_series_is_midline():
    out = sparkline([3, 3, 3, 3])
    assert set(out) == {BLOCKS[len(BLOCKS) // 2]}


def test_rising_series_ends_highest():
    out = sparkline([1, 2, 3, 4, 5])
    assert out[0] == BLOCKS[0]
    assert out[-1] == BLOCKS[-1]


def test_downsample_respects_width():
    out = sparkline(list(range(100)), width=10)
    assert len(out) == 10


def test_ignores_none_values():
    out = sparkline([1, None, 5])
    assert len(out) == 2

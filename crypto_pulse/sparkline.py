"""Render a list of numbers as a compact unicode sparkline."""

from __future__ import annotations

from typing import List, Sequence

# Eight levels, low to high.
BLOCKS = "▁▂▃▄▅▆▇█"  # ▁▂▃▄▅▆▇█


def sparkline(values: Sequence[float], width: int = 0) -> str:
    """Turn ``values`` into a string of block characters.

    If ``width`` is given and smaller than ``len(values)``, the series is
    downsampled by averaging buckets so the sparkline fits a fixed column.
    """
    nums: List[float] = [float(v) for v in values if v is not None]
    if not nums:
        return ""
    if len(nums) == 1:
        return BLOCKS[len(BLOCKS) // 2]

    if width and width > 0 and len(nums) > width:
        nums = _downsample(nums, width)

    low = min(nums)
    high = max(nums)
    span = high - low
    if span == 0:
        return BLOCKS[len(BLOCKS) // 2] * len(nums)

    out = []
    last = len(BLOCKS) - 1
    for value in nums:
        idx = int(round((value - low) / span * last))
        out.append(BLOCKS[max(0, min(last, idx))])
    return "".join(out)


def _downsample(values: List[float], width: int) -> List[float]:
    """Bucket-average ``values`` down to ``width`` points."""
    bucket = len(values) / float(width)
    result: List[float] = []
    for i in range(width):
        start = int(i * bucket)
        end = int((i + 1) * bucket) or start + 1
        chunk = values[start:end] or [values[min(start, len(values) - 1)]]
        result.append(sum(chunk) / len(chunk))
    return result

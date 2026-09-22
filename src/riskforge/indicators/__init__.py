"""技术/统计指标库（M2）。

所有指标都是**纯函数**：输入一维数值序列，输出与之**等长、按位置对齐**的序列，
预热期（数据不足的位置）用 ``None`` 表示。仅依赖 Python 标准库，结果确定、可复现。

约定：
- 均线类窗口 ``w`` 表示"最近 w 个值（含当前）"，首个有效下标为 ``w-1``；
- 不做任何前向填充，预热期明确为 ``None``，避免把未来信息泄漏给策略。
"""
from riskforge.indicators.core import (
    atr,
    bollinger,
    ema,
    macd,
    rolling_max,
    rolling_min,
    rolling_std,
    rsi,
    sma,
    true_ranges,
)

__all__ = [
    "sma",
    "ema",
    "rolling_std",
    "rolling_max",
    "rolling_min",
    "bollinger",
    "rsi",
    "macd",
    "true_ranges",
    "atr",
]

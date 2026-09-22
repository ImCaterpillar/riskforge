"""双均线（金叉/死叉）策略，long-only。"""
from __future__ import annotations

from typing import List

from riskforge.data.bars import BarSeries
from riskforge.indicators.core import sma
from riskforge.strategy.base import SignalEvent, Strategy
from riskforge.types import Signal


class MovingAverageCross(Strategy):
    """快线上穿慢线（金叉）入场，快线下穿慢线（死叉）离场。

    只做多：金叉发 LONG，死叉发 FLAT；信号按状态去重，不会连续重复入场。
    """

    name = "ma-cross"

    def __init__(self, fast: int = 10, slow: int = 30) -> None:
        if not (0 < fast < slow):
            raise ValueError("要求 0 < fast < slow")
        self.fast = fast
        self.slow = slow

    def describe(self) -> str:
        return f"ma-cross(fast={self.fast}, slow={self.slow})"

    def generate(self, series: BarSeries) -> List[SignalEvent]:
        closes = [b.close for b in series]
        fast_line = sma(closes, self.fast)
        slow_line = sma(closes, self.slow)
        events: List[SignalEvent] = []
        in_pos = False
        for i in range(1, len(closes)):
            if fast_line[i] is None or slow_line[i] is None:
                continue
            if fast_line[i - 1] is None or slow_line[i - 1] is None:
                continue
            crossed_up = fast_line[i - 1] <= slow_line[i - 1] and fast_line[i] > slow_line[i]
            crossed_down = fast_line[i - 1] >= slow_line[i - 1] and fast_line[i] < slow_line[i]
            bar = series[i]
            if crossed_up and not in_pos:
                events.append(SignalEvent(
                    series.symbol, bar.date, Signal.LONG, bar.close,
                    f"金叉：MA{self.fast}={fast_line[i]:.4f} 上穿 MA{self.slow}={slow_line[i]:.4f}",
                ))
                in_pos = True
            elif crossed_down and in_pos:
                events.append(SignalEvent(
                    series.symbol, bar.date, Signal.FLAT, bar.close,
                    f"死叉：MA{self.fast}={fast_line[i]:.4f} 下穿 MA{self.slow}={slow_line[i]:.4f}",
                ))
                in_pos = False
        return events

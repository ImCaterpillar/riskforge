"""RSI 超卖回升（均值回归）策略，long-only。"""
from __future__ import annotations

from typing import List

from riskforge.data.bars import BarSeries
from riskforge.indicators.core import rsi
from riskforge.strategy.base import SignalEvent, Strategy
from riskforge.types import Signal


class RsiReversion(Strategy):
    """RSI 从超卖区向上回到 ``oversold`` 之上时入场（确认回升，而非徒手接刀）；
    RSI 升到 ``overbought`` 及以上时离场。"""

    name = "rsi-reversion"

    def __init__(self, period: int = 14, oversold: float = 30.0,
                 overbought: float = 70.0) -> None:
        if period < 1:
            raise ValueError("period 必须 >= 1")
        if not (0.0 < oversold < overbought < 100.0):
            raise ValueError("要求 0 < oversold < overbought < 100")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def describe(self) -> str:
        return (f"rsi-reversion(period={self.period}, "
                f"oversold={self.oversold}, overbought={self.overbought})")

    def generate(self, series: BarSeries) -> List[SignalEvent]:
        closes = [b.close for b in series]
        line = rsi(closes, self.period)
        events: List[SignalEvent] = []
        in_pos = False
        for i in range(1, len(closes)):
            if line[i] is None or line[i - 1] is None:
                continue
            bar = series[i]
            rose_from_oversold = line[i - 1] < self.oversold and line[i] >= self.oversold
            if rose_from_oversold and not in_pos:
                events.append(SignalEvent(
                    series.symbol, bar.date, Signal.LONG, bar.close,
                    f"RSI({self.period}) 自超卖区回升至 {line[i]:.2f}",
                ))
                in_pos = True
            elif line[i] >= self.overbought and in_pos:
                events.append(SignalEvent(
                    series.symbol, bar.date, Signal.FLAT, bar.close,
                    f"RSI({self.period}) 升至超买区 {line[i]:.2f}",
                ))
                in_pos = False
        return events

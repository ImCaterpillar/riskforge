"""唐奇安通道（Donchian）突破策略，long-only。"""
from __future__ import annotations

from typing import List

from riskforge.data.bars import BarSeries
from riskforge.strategy.base import SignalEvent, Strategy
from riskforge.types import Signal


class DonchianBreakout(Strategy):
    """收盘价突破前 ``window`` 根（不含当前）最高价则入场，跌破前 window 根最低价则离场。

    用"不含当前 bar"的回看窗口，避免把当天极值既当阈值又当突破，造成未来函数。
    """

    name = "donchian"

    def __init__(self, window: int = 20) -> None:
        if window < 1:
            raise ValueError("window 必须 >= 1")
        self.window = window

    def describe(self) -> str:
        return f"donchian(window={self.window})"

    def generate(self, series: BarSeries) -> List[SignalEvent]:
        n = len(series)
        events: List[SignalEvent] = []
        in_pos = False
        for i in range(n):
            if i < self.window:
                continue
            prior = series[i - self.window: i]
            upper = max(b.high for b in prior)
            lower = min(b.low for b in prior)
            bar = series[i]
            if bar.close > upper and not in_pos:
                events.append(SignalEvent(
                    series.symbol, bar.date, Signal.LONG, bar.close,
                    f"向上突破 {self.window} 日通道上轨 {upper:.4f}",
                ))
                in_pos = True
            elif bar.close < lower and in_pos:
                events.append(SignalEvent(
                    series.symbol, bar.date, Signal.FLAT, bar.close,
                    f"向下跌破 {self.window} 日通道下轨 {lower:.4f}",
                ))
                in_pos = False
        return events

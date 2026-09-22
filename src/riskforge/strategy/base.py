"""策略基类与信号事件。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import List

from riskforge.data.bars import BarSeries
from riskforge.types import Signal

SIGNAL_CSV_FIELDS = ["date", "symbol", "signal", "price", "reason"]


@dataclass(frozen=True)
class SignalEvent:
    """一个离散交易信号。

    :param signal: LONG=开多/入场，FLAT=平多离场，SHORT=开空（本框架当前策略多为 long-only）。
    :param price: 信号触发参考价（通常为当日收盘），仅作记录，实际成交价由引擎决定。
    :param reason: 人类可读的触发原因，便于复核与回测日志。
    """

    symbol: str
    date: date
    signal: Signal
    price: float
    reason: str

    def to_row(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "symbol": self.symbol,
            "signal": self.signal.value,
            "price": f"{self.price:.6f}",
            "reason": self.reason,
        }


class Strategy(ABC):
    """策略接口。实现类负责把 ``BarSeries`` 转成信号列表。"""

    #: 策略名称（CLI / 报告展示用）
    name: str = "strategy"

    @abstractmethod
    def generate(self, series: BarSeries) -> List[SignalEvent]:
        """对单只标的的完整 K 线序列生成信号。"""

    # 便于在报告/CLI 里描述参数
    def describe(self) -> str:
        return self.name

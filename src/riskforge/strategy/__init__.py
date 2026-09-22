"""策略层（M2）：把行情 + 指标转成离散交易信号。

本层**只产出信号**，不碰资金、撮合与持仓（那是 M3 回测引擎的职责）。
所有策略实现 :class:`riskforge.strategy.base.Strategy` 接口，输入 ``BarSeries``，
输出按时间有序、去重的 :class:`SignalEvent` 列表。
"""
from riskforge.strategy.base import SignalEvent, Strategy
from riskforge.strategy.breakout import DonchianBreakout
from riskforge.strategy.ma_cross import MovingAverageCross
from riskforge.strategy.rsi_reversion import RsiReversion
from riskforge.strategy.runner import run_strategy, write_signals

__all__ = [
    "SignalEvent",
    "Strategy",
    "MovingAverageCross",
    "DonchianBreakout",
    "RsiReversion",
    "run_strategy",
    "write_signals",
]

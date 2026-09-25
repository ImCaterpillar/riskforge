"""可复现的合成行情生成器。

用途：

- 在**无网络/无数据**环境下为回测引擎、指标、风险计算提供确定性输入；
- 单元测试里用固定 seed 断言数值；
- 示例与文档的可运行演示。

价格服从带漂移的几何布朗运动（GBM），OHLC 关系与成交量都按行情语义构造，
保证生成结果能通过 :mod:`riskforge.data.validators` 的全部硬校验。
**合成数据仅用于测试/演示，不代表任何真实标的。**
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

from riskforge.data.bars import Bar
from riskforge.data.calendar import TradingCalendar
from riskforge.types import Frequency

_DT = 1.0 / 252.0  # 日频，每年约 252 个交易日


@dataclass(frozen=True, slots=True)
class GBMParams:
    """单只标的的 GBM 参数。"""

    s0: float = 100.0
    """期初价格。"""
    mu: float = 0.08
    """年化漂移（期望对数收益的年化均值口径）。"""
    sigma: float = 0.25
    """年化波动率。"""
    base_volume: float = 1_000_000.0
    """日均成交量基准。"""

    def __post_init__(self) -> None:
        if self.s0 <= 0:
            raise ValueError("s0 必须为正")
        if self.sigma < 0:
            raise ValueError("sigma 不能为负")
        if self.base_volume <= 0:
            raise ValueError("base_volume 必须为正")


def _session_dates(start: date, ndays: int, calendar: TradingCalendar) -> List[date]:
    """从 start 起取 ndays 个交易日（start 非交易日则顺延到下一交易日）。"""
    if ndays < 1:
        raise ValueError("ndays 至少为 1")
    first = start if calendar.is_trading_day(start) else calendar.next_trading_day(start)
    dates = [first]
    cur = first
    while len(dates) < ndays:
        cur = calendar.next_trading_day(cur)
        dates.append(cur)
    return dates


def generate_bars(
    symbol: str,
    start: date,
    ndays: int,
    params: Optional[GBMParams] = None,
    seed: Optional[int] = None,
    calendar: Optional[TradingCalendar] = None,
    freq: Frequency = Frequency.DAILY,
) -> List[Bar]:
    """生成 ndays 根日 K 线。

    ``seed`` 固定时结果完全确定。相同 (symbol 序列顺序, seed, 参数) 必须产生相同行情，
    不同 symbol 应派生不同子流以避免多标的完全相关。
    """
    params = params or GBMParams()
    calendar = calendar or TradingCalendar()
    rng = random.Random(seed)
    dates = _session_dates(start, ndays, calendar)

    sqrt_dt = math.sqrt(_DT)
    drift = (params.mu - 0.5 * params.sigma * params.sigma) * _DT
    vol = params.sigma * sqrt_dt
    gap_vol = 0.25 * vol  # 隔夜跳空波动约为日内波动的 1/4

    bars: List[Bar] = []
    prev_close = params.s0
    for d in dates:
        # 开盘：相对前收的隔夜跳空
        open_ = prev_close * math.exp(rng.gauss(0.0, gap_vol))
        # 收盘：GBM 一步
        close = prev_close * math.exp(drift + vol * rng.gauss(0.0, 1.0))
        # 日内振幅：用两个独立半正态给出上/下影
        up = abs(rng.gauss(0.0, 0.6 * vol))
        dn = abs(rng.gauss(0.0, 0.6 * vol))
        high = max(open_, close) * (1.0 + up)
        low = min(open_, close) * (1.0 - dn)
        # 防止极端抽样导致低价非正
        low = max(low, min(open_, close) * 1e-6)
        # 成交量随价格波动放大
        ret = close / prev_close - 1.0
        vol_mult = math.exp(rng.gauss(0.0, 0.25)) * (1.0 + 8.0 * abs(ret))
        volume = max(1.0, round(params.base_volume * vol_mult))
        vwap = (open_ + high + low + close) / 4.0
        amount = volume * vwap
        bars.append(
            Bar(
                symbol=symbol,
                date=d,
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=float(volume),
                amount=amount,
            )
        )
        prev_close = close
    return bars


def generate_panel(
    spec: Dict[str, GBMParams],
    start: date,
    ndays: int,
    seed: int = 7,
    calendar: Optional[TradingCalendar] = None,
) -> Dict[str, List[Bar]]:
    """一次生成多只标的（共享交易日历，价格流相互独立）。

    spec 为 {symbol: GBMParams}；为保证可复现，按 symbol 名排序后，
    用 ``seed + 稳定偏移`` 派生各标的的随机种子。
    """
    calendar = calendar or TradingCalendar()
    out: Dict[str, List[Bar]] = {}
    for i, symbol in enumerate(sorted(spec)):
        out[symbol] = generate_bars(
            symbol,
            start,
            ndays,
            params=spec[symbol],
            seed=seed * 1000003 + i * 97 + symbol.__len__(),
            calendar=calendar,
        )
    return out

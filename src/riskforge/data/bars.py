"""K 线（Bar）数据结构与序列容器。

序列容器只做**与行情语义一致**的计算（收益率、切片、复权价），不引入任何第三方依赖。
复权价通过 :class:`Bar` 上的 ``adj_factor`` 表达，默认 1.0（不复权）。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Iterator, List, Optional, Sequence

from riskforge.types import Frequency


@dataclass(frozen=True, slots=True)
class Bar:
    """一根日 K 线（价格均为未复权原始价）。"""

    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = None
    """成交额（可选）。"""
    adj_factor: float = 1.0
    """后复权累计因子，默认 1.0；由复权模块计算。"""

    def __post_init__(self) -> None:
        if not isinstance(self.date, date):
            raise TypeError(f"date 必须是 datetime.date，得到 {type(self.date)!r}")
        for name in ("open", "high", "low", "close"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} 必须为正数，得到 {value!r}")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError(
                f"{self.symbol} {self.date} OHLC 关系非法："
                f"low={self.low} open={self.open} close={self.close} high={self.high}"
            )
        if self.volume < 0 or not math.isfinite(self.volume):
            raise ValueError(f"volume 必须非负有限，得到 {self.volume!r}")
        if self.adj_factor <= 0 or not math.isfinite(self.adj_factor):
            raise ValueError(f"adj_factor 必须为正数，得到 {self.adj_factor!r}")

    # ---- 复权价格 ----
    @property
    def adj_open(self) -> float:
        return self.open * self.adj_factor

    @property
    def adj_high(self) -> float:
        return self.high * self.adj_factor

    @property
    def adj_low(self) -> float:
        return self.low * self.adj_factor

    @property
    def adj_close(self) -> float:
        return self.close * self.adj_factor

    def to_row(self) -> dict:
        """序列化为 CSV 友好的扁平字典。"""
        return {
            "date": self.date.isoformat(),
            "open": f"{self.open:.6f}",
            "high": f"{self.high:.6f}",
            "low": f"{self.low:.6f}",
            "close": f"{self.close:.6f}",
            "volume": f"{self.volume:.2f}",
            "amount": "" if self.amount is None else f"{self.amount:.2f}",
            "adj_factor": f"{self.adj_factor:.8f}",
        }


class BarSeries:
    """某只标的在单一频率下、按日期升序排列的 K 线集合。"""

    __slots__ = ("symbol", "freq", "_bars", "_index")

    def __init__(
        self,
        symbol: str,
        bars: Sequence[Bar] = (),
        freq: Frequency = Frequency.DAILY,
    ) -> None:
        self.symbol = symbol
        self.freq = freq
        self._bars: List[Bar] = []
        self._index: dict[date, int] = {}
        for bar in bars:
            self.append(bar)

    # ---- 容器协议 ----
    def __len__(self) -> int:
        return len(self._bars)

    def __iter__(self) -> Iterator[Bar]:
        return iter(self._bars)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return BarSeries(self.symbol, self._bars[key], self.freq)
        if isinstance(key, date):
            return self._bars[self._index[key]]
        return self._bars[key]

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, BarSeries)
            and self.symbol == other.symbol
            and self.freq == other.freq
            and self._bars == other._bars
        )

    # ---- 变更 ----
    def append(self, bar: Bar) -> None:
        if bar.symbol != self.symbol:
            raise ValueError(f"标的不一致：序列 {self.symbol} 收到 {bar.symbol}")
        if self._bars:
            last = self._bars[-1]
            if bar.date < last.date:
                raise ValueError(f"日期必须升序：{bar.date} 早于末尾 {last.date}")
            if bar.date == last.date:
                raise ValueError(f"日期重复：{bar.date}")
        if bar.date in self._index:
            raise ValueError(f"日期重复：{bar.date}")
        self._index[bar.date] = len(self._bars)
        self._bars.append(bar)

    # ---- 基本访问 ----
    @property
    def dates(self) -> List[date]:
        return [b.date for b in self._bars]

    def field(self, name: str, adjusted: bool = False) -> List[float]:
        """取某一字段序列；adjusted=True 时对价格字段乘复权因子。"""
        price_fields = {"open", "high", "low", "close"}
        out: List[float] = []
        for b in self._bars:
            value = getattr(b, name)
            if adjusted and name in price_fields:
                value = value * b.adj_factor
            out.append(value)
        return out

    @property
    def closes(self) -> List[float]:
        return [b.close for b in self._bars]

    @property
    def adj_closes(self) -> List[float]:
        return [b.adj_close for b in self._bars]

    def loc(self, d: date) -> Bar:
        return self._bars[self._index[d]]

    def get(self, d: date) -> Optional[Bar]:
        idx = self._index.get(d)
        return None if idx is None else self._bars[idx]

    def between(self, start: date, end: date) -> "BarSeries":
        """返回闭区间 [start, end] 内的子序列。"""
        sub = [b for b in self._bars if start <= b.date <= end]
        return BarSeries(self.symbol, sub, self.freq)

    # ---- 收益序列 ----
    def simple_returns(self, adjusted: bool = True) -> List[float]:
        """逐期简单收益率 r_t = P_t / P_{t-1} - 1，长度 = n-1。"""
        prices = self.adj_closes if adjusted else self.closes
        return [prices[i] / prices[i - 1] - 1.0 for i in range(1, len(prices))]

    def log_returns(self, adjusted: bool = True) -> List[float]:
        """逐期对数收益率，长度 = n-1。"""
        prices = self.adj_closes if adjusted else self.closes
        return [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]

    def total_return(self, adjusted: bool = True) -> float:
        """区间总收益率（末/初 - 1）；不足两根 K 线返回 0。"""
        prices = self.adj_closes if adjusted else self.closes
        if len(prices) < 2 or prices[0] == 0:
            return 0.0
        return prices[-1] / prices[0] - 1.0

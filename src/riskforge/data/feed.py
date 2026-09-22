"""数据源：CSV 文件源与合成行情源。

CSV 约定（每只标的一个 ``<symbol>.csv``，UTF-8、首行表头）：

    date,open,high,low,close,volume,amount,adj_factor

``amount`` 可空；``adj_factor`` 缺省为 1.0。读取后**不会自动校验**，
调用方应显式跑 :func:`riskforge.data.validators.validate_bars`。
"""
from __future__ import annotations

import csv
import os
from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List, Optional

from riskforge.data.bars import Bar, BarSeries
from riskforge.data.calendar import TradingCalendar
from riskforge.data.synthetic import GBMParams, generate_panel
from riskforge.types import Frequency

FIELDNAMES = ["date", "open", "high", "low", "close", "volume", "amount", "adj_factor"]


def _safe_symbol(symbol: str) -> str:
    if not symbol or any(ch in symbol for ch in '/\\:*?"<>|'):
        raise ValueError(f"非法标的代码（不能含路径分隔符/通配符）：{symbol!r}")
    return symbol


class DataFeed(ABC):
    """统一数据源接口。"""

    @abstractmethod
    def symbols(self) -> List[str]:
        """返回可用标的代码（排序后）。"""

    @abstractmethod
    def get(self, symbol: str) -> BarSeries:
        """取某标的的完整日 K 序列。"""


class CsvFeed(DataFeed):
    """以目录下每标的一个 CSV 的方式持久化行情。"""

    def __init__(self, root_dir: str, freq: Frequency = Frequency.DAILY) -> None:
        self.root_dir = root_dir
        self.freq = freq
        os.makedirs(root_dir, exist_ok=True)

    def path_for(self, symbol: str) -> str:
        _safe_symbol(symbol)
        return os.path.join(self.root_dir, f"{symbol}.csv")

    def symbols(self) -> List[str]:
        if not os.path.isdir(self.root_dir):
            return []
        return sorted(
            fn[:-4]
            for fn in os.listdir(self.root_dir)
            if fn.endswith(".csv") and not fn.startswith(".")
        )

    def write(self, symbol: str, series: BarSeries) -> str:
        """把序列写成 CSV，返回文件路径。"""
        path = self.path_for(symbol)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
            writer.writeheader()
            for bar in series:
                writer.writerow(bar.to_row())
        return path

    def load(self, symbol: str) -> BarSeries:
        path = self.path_for(symbol)
        bars: List[Bar] = []
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            missing = {"date", "open", "high", "low", "close", "volume"} - set(
                reader.fieldnames or []
            )
            if missing:
                raise ValueError(f"{symbol}.csv 缺少必需列：{sorted(missing)}")
            for row in reader:
                amount_raw = (row.get("amount") or "").strip()
                adj_raw = (row.get("adj_factor") or "").strip()
                bars.append(
                    Bar(
                        symbol=symbol,
                        date=date.fromisoformat(row["date"].strip()),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row["volume"]),
                        amount=float(amount_raw) if amount_raw else None,
                        adj_factor=float(adj_raw) if adj_raw else 1.0,
                    )
                )
        return BarSeries(symbol, bars, self.freq)

    def get(self, symbol: str) -> BarSeries:
        return self.load(symbol)

    def load_all(self) -> Dict[str, BarSeries]:
        return {s: self.load(s) for s in self.symbols()}


class SyntheticFeed(DataFeed):
    """离线、可复现的合成数据源。"""

    def __init__(
        self,
        spec: Dict[str, GBMParams],
        start: date,
        ndays: int,
        seed: int = 7,
        calendar: Optional[TradingCalendar] = None,
    ) -> None:
        if not spec:
            raise ValueError("spec 至少要包含一只标的")
        self._panel = generate_panel(spec, start, ndays, seed=seed, calendar=calendar)

    def symbols(self) -> List[str]:
        return sorted(self._panel)

    def get(self, symbol: str) -> BarSeries:
        if symbol not in self._panel:
            raise KeyError(f"合成数据源中没有 {symbol}；可用 {self.symbols()}")
        return BarSeries(symbol, self._panel[symbol])

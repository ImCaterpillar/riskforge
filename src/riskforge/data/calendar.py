"""交易日历。

默认把周一至周五视为交易日，节假日通过集合显式给出（可从每行一个 ISO 日期的
文本文件加载）。日历不依赖任何第三方库，也不内置交易所数据，避免把易过期的
节假日表硬编码进核心。
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, List, Set, Tuple


class TradingCalendar:
    """以周掩码 + 节假日集合定义的交易日历。"""

    def __init__(
        self,
        holidays: Iterable[date] = (),
        weekmask: Tuple[int, ...] = (0, 1, 2, 3, 4),
    ) -> None:
        self.weekmask = set(weekmask)
        self.holidays: Set[date] = set(holidays)

    # ---- 构造 ----
    @classmethod
    def from_file(cls, path: str, weekmask: Tuple[int, ...] = (0, 1, 2, 3, 4)) -> "TradingCalendar":
        """从文本文件加载节假日：每行一个 ``YYYY-MM-DD``，``#`` 开头为注释。"""
        holidays: List[date] = []
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                holidays.append(date.fromisoformat(line))
        return cls(holidays, weekmask)

    def add_holidays(self, days: Iterable[date]) -> None:
        self.holidays.update(days)

    # ---- 查询 ----
    def is_trading_day(self, d: date) -> bool:
        return d.weekday() in self.weekmask and d not in self.holidays

    def next_trading_day(self, d: date, n: int = 1) -> date:
        """返回 d 之后第 n 个交易日（n>=1，不含 d 本身）。"""
        if n < 1:
            raise ValueError("n 必须 >= 1")
        cur = d
        found = 0
        step = timedelta(days=1)
        while found < n:
            cur = cur + step
            if self.is_trading_day(cur):
                found += 1
        return cur

    def prev_trading_day(self, d: date, n: int = 1) -> date:
        """返回 d 之前第 n 个交易日（n>=1，不含 d 本身）。"""
        if n < 1:
            raise ValueError("n 必须 >= 1")
        cur = d
        found = 0
        step = timedelta(days=-1)
        while found < n:
            cur = cur + step
            if self.is_trading_day(cur):
                found += 1
        return cur

    def trading_days(self, start: date, end: date) -> List[date]:
        """返回闭区间 [start, end] 内的全部交易日（升序）。"""
        if end < start:
            raise ValueError(f"end {end} 早于 start {start}")
        out: List[date] = []
        cur = start
        step = timedelta(days=1)
        while cur <= end:
            if self.is_trading_day(cur):
                out.append(cur)
            cur = cur + step
        return out

    def count_sessions(self, start: date, end: date) -> int:
        """闭区间内交易日数量。"""
        return len(self.trading_days(start, end))

    def missing_sessions(self, dates: Iterable[date]) -> List[date]:
        """给定一组实际有行情的日期，返回区间内"应有却缺失"的交易日。

        用于数据完整性校验：只在首个与最后一个有行情日期之间检查，
        不把上市前/退市后的正常空白天数误报为缺口。
        """
        ds = sorted(set(dates))
        if len(ds) < 2:
            return []
        expected = set(self.trading_days(ds[0], ds[-1]))
        present = set(ds)
        return sorted(expected - present)

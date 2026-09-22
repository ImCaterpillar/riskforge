"""行情数据入库前校验。

硬错误（``severity="error"``）会让数据不可用于回测；缺口类问题标为 ``warning``，
由调用方决定是否容忍。校验器只依据行情自身语义，不假设标的或市场。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Sequence

from riskforge.data.bars import Bar
from riskforge.data.calendar import TradingCalendar


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """一条校验发现。"""

    code: str
    severity: str  # "error" | "warning"
    date: Optional[date]
    message: str

    def __str__(self) -> str:
        when = "" if self.date is None else f" {self.date}"
        return f"[{self.severity.upper()}]{when} {self.code}: {self.message}"


def _check_ohlc(bar: Bar) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    prices = {"open": bar.open, "high": bar.high, "low": bar.low, "close": bar.close}
    for name, value in prices.items():
        if not math.isfinite(value) or value <= 0:
            issues.append(ValidationIssue("NON_POSITIVE_PRICE", "error", bar.date,
                                          f"{name}={value} 非正或非有限"))
    if math.isfinite(bar.high) and math.isfinite(bar.low):
        if bar.high < bar.low:
            issues.append(ValidationIssue("HIGH_LOW", "error", bar.date,
                                          f"high={bar.high} < low={bar.low}"))
        hi_ok = math.isfinite(bar.open) and math.isfinite(bar.close)
        if hi_ok and bar.high < max(bar.open, bar.close):
            issues.append(ValidationIssue("HIGH_NOT_MAX", "error", bar.date,
                                          "high 未同时 >= open/close"))
        if hi_ok and bar.low > min(bar.open, bar.close):
            issues.append(ValidationIssue("LOW_NOT_MIN", "error", bar.date,
                                          "low 未同时 <= open/close"))
    if not math.isfinite(bar.volume) or bar.volume < 0:
        issues.append(ValidationIssue("BAD_VOLUME", "error", bar.date,
                                      f"volume={bar.volume} 为负或非有限"))
    if not math.isfinite(bar.adj_factor) or bar.adj_factor <= 0:
        issues.append(ValidationIssue("BAD_ADJ_FACTOR", "error", bar.date,
                                      f"adj_factor={bar.adj_factor} 非正"))
    return issues


def validate_bars(
    bars: Sequence[Bar],
    calendar: Optional[TradingCalendar] = None,
    check_sessions: bool = True,
) -> List[ValidationIssue]:
    """对一组（应为同一标的、按日期升序的）K 线做校验。

    返回全部发现；空列表表示无问题。``error`` 必须在数据进入引擎前解决。
    """
    issues: List[ValidationIssue] = []
    if not bars:
        return [ValidationIssue("EMPTY", "error", None, "K 线序列为空")]

    symbols = {b.symbol for b in bars}
    if len(symbols) > 1:
        issues.append(ValidationIssue("MIXED_SYMBOL", "error", None,
                                      f"序列混入多个标的：{sorted(symbols)}"))

    prev: Optional[Bar] = None
    seen: set[date] = set()
    for bar in bars:
        issues.extend(_check_ohlc(bar))
        if bar.date in seen:
            issues.append(ValidationIssue("DUP_DATE", "error", bar.date, "日期重复"))
        seen.add(bar.date)
        if prev is not None and bar.date < prev.date:
            issues.append(ValidationIssue("NOT_SORTED", "error", bar.date,
                                          f"日期早于前一根 {prev.date}"))
        # 单日涨跌幅异常（>60%）多为拆分未复权或数据错误，给警告
        if prev is not None and prev.close > 0:
            chg = abs(bar.close / prev.close - 1.0)
            if chg > 0.6:
                issues.append(ValidationIssue("ABNORMAL_JUMP", "warning", bar.date,
                                              f"相对前收变动 {chg:.1%}，疑似未复权或脏数据"))
        prev = bar

    if check_sessions and calendar is not None and len(bars) >= 2:
        missing = calendar.missing_sessions([b.date for b in bars])
        # 停牌等会造成真实缺口，这里只提示，不判错
        for d in missing:
            issues.append(ValidationIssue("MISSING_SESSION", "warning", d,
                                          "交易日历上应有行情但该日无 K 线（可能停牌/缺数据）"))
    return issues


def has_errors(issues: Sequence[ValidationIssue]) -> bool:
    return any(i.severity == "error" for i in issues)

"""策略运行与信号落盘。"""
from __future__ import annotations

import csv
import os
from typing import List

from riskforge.data.bars import BarSeries
from riskforge.strategy.base import SIGNAL_CSV_FIELDS, SignalEvent, Strategy


def run_strategy(strategy: Strategy, series: BarSeries) -> List[SignalEvent]:
    """运行策略并做结果合法性校验（时间有序、同日不重复、标的一致）。"""
    events = list(strategy.generate(series))
    last_date = None
    for ev in events:
        if ev.symbol != series.symbol:
            raise ValueError(f"信号标的 {ev.symbol} 与序列标的 {series.symbol} 不一致")
        if last_date is not None and ev.date <= last_date:
            raise ValueError(f"信号日期必须严格递增：{last_date} -> {ev.date}")
        last_date = ev.date
    return events


def write_signals(path: str, events: List[SignalEvent]) -> str:
    """把信号写成 CSV（表头 date,symbol,signal,price,reason），返回路径。"""
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=SIGNAL_CSV_FIELDS)
        writer.writeheader()
        for ev in events:
            writer.writerow(ev.to_row())
    return path


def read_signals(path: str) -> List[dict]:
    """读回信号 CSV（测试/报告用）。"""
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))

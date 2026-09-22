"""对 data/samples 的合成样例跑三种策略，把信号写成 CSV（离线、可复现）。

运行：
    python examples/run_signals.py
输出 data/samples/DEMO.<strategy>.signals.csv。信号基于 GBM 假数据，仅作演示。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from riskforge.data.feed import CsvFeed  # noqa: E402
from riskforge.strategy import (  # noqa: E402
    DonchianBreakout,
    MovingAverageCross,
    RsiReversion,
    run_strategy,
    write_signals,
)

ROOT = os.path.join(os.path.dirname(__file__), "..", "data", "samples")
SYMBOL = "DEMO"

STRATEGIES = {
    "ma-cross": MovingAverageCross(fast=10, slow=30),
    "donchian": DonchianBreakout(window=20),
    "rsi-reversion": RsiReversion(period=14, oversold=30, overbought=70),
}


def main() -> int:
    feed = CsvFeed(ROOT)
    series = feed.load(SYMBOL)
    for name, strat in STRATEGIES.items():
        events = run_strategy(strat, series)
        out = os.path.join(ROOT, f"{SYMBOL}.{name}.signals.csv")
        write_signals(out, events)
        print(f"{strat.describe():42s} -> {len(events)} 个信号 -> {os.path.normpath(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""生成 data/samples 下的合成样例数据（离线、可复现）。

运行：
    python examples/generate_sample_data.py
输出 data/samples/DEMO.csv 与 data/samples/BETA.csv。数据为 GBM 假数据，非真实标的。
"""
from __future__ import annotations

import os
import sys
from datetime import date

# 允许直接从仓库根目录运行而无需安装
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from riskforge.data.bars import BarSeries  # noqa: E402
from riskforge.data.calendar import TradingCalendar  # noqa: E402
from riskforge.data.feed import CsvFeed  # noqa: E402
from riskforge.data.synthetic import GBMParams, generate_panel  # noqa: E402


def main() -> int:
    root = os.path.join(os.path.dirname(__file__), "..", "data", "samples")
    spec = {
        "DEMO": GBMParams(s0=100.0, mu=0.08, sigma=0.22),
        "BETA": GBMParams(s0=50.0, mu=0.05, sigma=0.35, base_volume=2_000_000),
    }
    panel = generate_panel(spec, date(2024, 1, 2), 126, seed=7,
                           calendar=TradingCalendar())
    feed = CsvFeed(root)
    for name in sorted(panel):
        path = feed.write(name, BarSeries(name, panel[name]))
        print(f"written {name}: {len(panel[name])} bars -> {os.path.normpath(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

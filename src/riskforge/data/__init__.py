"""市场数据层（M1）。

提供：

- :class:`~riskforge.data.bars.Bar` / :class:`~riskforge.data.bars.BarSeries`：K 线与序列；
- :class:`~riskforge.data.calendar.TradingCalendar`：交易日历；
- :mod:`riskforge.data.synthetic`：可复现的合成行情（离线测试与演示）；
- :class:`~riskforge.data.feed.CsvFeed` / :class:`SyntheticFeed`：数据源；
- :mod:`riskforge.data.adjust`：拆股/分红复权；
- :mod:`riskforge.data.validators`：入库前数据校验。
"""

from riskforge.data.bars import Bar, BarSeries
from riskforge.data.calendar import TradingCalendar
from riskforge.data.feed import CsvFeed, DataFeed, SyntheticFeed

__all__ = [
    "Bar",
    "BarSeries",
    "TradingCalendar",
    "DataFeed",
    "CsvFeed",
    "SyntheticFeed",
]

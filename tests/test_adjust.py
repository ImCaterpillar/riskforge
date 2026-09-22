import context  # noqa: F401
import unittest
from datetime import date

from riskforge.data.adjust import CorporateAction, apply_actions
from riskforge.data.bars import Bar
from riskforge.data.calendar import TradingCalendar


def _flat(dates, price_before, price_after, ex):
    bars = []
    for d in dates:
        p = price_before if d < ex else price_after
        bars.append(Bar("X", d, p, p, p, p, 1000.0))
    return bars


class AdjustTest(unittest.TestCase):
    def setUp(self):
        self.cal = TradingCalendar()
        self.dates = self.cal.trading_days(date(2024, 1, 2), date(2024, 1, 15))
        self.ex = self.dates[4]

    def test_split_continuity(self):
        # 2:1 拆股：除权日起未复权价从 100 机械腰斩到 50
        bars = _flat(self.dates, 100.0, 50.0, self.ex)
        out = apply_actions(bars, [CorporateAction(self.ex, "split", 2.0)])
        adj_closes = [round(b.adj_close, 8) for b in out]
        # 复权后全程 50，除权日无跳空
        self.assertTrue(all(abs(c - 50.0) < 1e-9 for c in adj_closes), adj_closes)
        rets = BarSeriesWrap(out).simple_returns(adjusted=True)
        self.assertTrue(all(abs(r) < 1e-12 for r in rets), rets)
        # 未复权在除权日确实有 -50% 跳空，证明测试有效
        raw_rets = BarSeriesWrap(out).simple_returns(adjusted=False)
        self.assertAlmostEqual(min(raw_rets), -0.5, places=9)

    def test_dividend_continuity(self):
        # 每股派现 1：除权前收盘 100，除权日起未复权价 99
        bars = _flat(self.dates, 100.0, 99.0, self.ex)
        out = apply_actions(bars, [CorporateAction(self.ex, "dividend", 1.0)])
        adj_closes = [round(b.adj_close, 8) for b in out]
        self.assertTrue(all(abs(c - 99.0) < 1e-9 for c in adj_closes), adj_closes)
        rets = BarSeriesWrap(out).simple_returns(adjusted=True)
        self.assertTrue(all(abs(r) < 1e-12 for r in rets), rets)

    def test_overlarge_dividend_rejected(self):
        bars = _flat(self.dates, 100.0, 10.0, self.ex)
        with self.assertRaises(ValueError):
            apply_actions(bars, [CorporateAction(self.ex, "dividend", 150.0)])


def BarSeriesWrap(bars):
    from riskforge.data.bars import BarSeries
    return BarSeries("X", bars)


if __name__ == "__main__":
    unittest.main()

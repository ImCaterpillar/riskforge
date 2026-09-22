import context  # noqa: F401
import unittest
from datetime import date

from riskforge.data.calendar import TradingCalendar
from riskforge.data.synthetic import GBMParams, generate_bars, generate_panel


class SyntheticTest(unittest.TestCase):
    def setUp(self):
        self.cal = TradingCalendar()
        self.start = date(2024, 1, 2)

    def test_determinism(self):
        a = generate_bars("X", self.start, 60, seed=42, calendar=self.cal)
        b = generate_bars("X", self.start, 60, seed=42, calendar=self.cal)
        self.assertEqual([x.close for x in a], [x.close for x in b])

    def test_seed_changes_path(self):
        a = generate_bars("X", self.start, 60, seed=1, calendar=self.cal)
        b = generate_bars("X", self.start, 60, seed=2, calendar=self.cal)
        self.assertNotEqual([x.close for x in a], [x.close for x in b])

    def test_count_and_trading_days(self):
        bars = generate_bars("X", date(2024, 1, 1), 30, seed=4, calendar=self.cal)
        self.assertEqual(len(bars), 30)
        dates = [x.date for x in bars]
        self.assertEqual(dates, sorted(set(dates)))
        self.assertTrue(all(self.cal.is_trading_day(d) for d in dates))

    def test_zero_vol_driftless_is_constant(self):
        bars = generate_bars(
            "X", self.start, 20,
            params=GBMParams(s0=80.0, mu=0.0, sigma=0.0), seed=9, calendar=self.cal,
        )
        self.assertTrue(all(abs(b.close - 80.0) < 1e-9 for b in bars))
        self.assertTrue(all(abs(b.open - 80.0) < 1e-9 for b in bars))

    def test_ohlc_relationship_and_positive(self):
        bars = generate_bars("X", self.start, 120, seed=11, calendar=self.cal)
        for b in bars:
            self.assertLessEqual(b.low, min(b.open, b.close))
            self.assertGreaterEqual(b.high, max(b.open, b.close))
            self.assertGreater(b.low, 0)
            self.assertGreater(b.volume, 0)

    def test_panel_symbols_independent(self):
        panel = generate_panel(
            {"AAA": GBMParams(), "BBB": GBMParams(s0=50, sigma=0.4)},
            self.start, 40, seed=5, calendar=self.cal,
        )
        self.assertEqual(sorted(panel), ["AAA", "BBB"])
        self.assertNotEqual(
            [x.close for x in panel["AAA"]], [x.close for x in panel["BBB"]]
        )


if __name__ == "__main__":
    unittest.main()

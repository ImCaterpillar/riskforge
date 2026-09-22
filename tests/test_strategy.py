import context  # noqa: F401
import os
import tempfile
import unittest
from datetime import date

from riskforge.data.bars import Bar, BarSeries
from riskforge.data.calendar import TradingCalendar
from riskforge.strategy import (
    DonchianBreakout,
    MovingAverageCross,
    RsiReversion,
    SignalEvent,
    run_strategy,
    write_signals,
)
from riskforge.types import Signal

CAL = TradingCalendar()
DATES = CAL.trading_days(date(2024, 1, 1), date(2024, 6, 30))


def series_from(closes, symbol="X"):
    bars = []
    for d, c in zip(DATES, closes):
        bars.append(Bar(symbol, d, float(c), float(c), float(c), float(c), 1000.0))
    return BarSeries(symbol, bars)


class MovingAverageCrossTest(unittest.TestCase):
    def test_golden_then_death_cross(self):
        # 长期横盘 -> 急涨（金叉）-> 急跌（死叉）
        closes = [100.0] * 12 + [102, 105, 109, 114, 120, 127, 135] \
            + [128, 120, 111, 102, 93, 84]
        s = series_from(closes)
        events = run_strategy(MovingAverageCross(3, 5), s)
        kinds = [e.signal for e in events]
        self.assertIn(Signal.LONG, kinds)
        self.assertIn(Signal.FLAT, kinds)
        first_long = next(i for i, k in enumerate(kinds) if k == Signal.LONG)
        first_flat = next(i for i, k in enumerate(kinds) if k == Signal.FLAT)
        self.assertLess(first_long, first_flat)
        # 信号日期严格递增、价格等于当日收盘、原因非空
        self.assertEqual([e.date for e in events], sorted({e.date for e in events}))
        for e in events:
            self.assertEqual(e.price, s.loc(e.date).close)
            self.assertTrue(e.reason)

    def test_bad_params(self):
        with self.assertRaises(ValueError):
            MovingAverageCross(30, 10)

    def test_flat_market_no_signals(self):
        s = series_from([50.0] * 40)
        self.assertEqual(run_strategy(MovingAverageCross(5, 20), s), [])


class DonchianTest(unittest.TestCase):
    def test_breakout_and_breakdown(self):
        closes = [10.0] * 12 + [20.0] + [20.0] * 6 + [5.0]
        s = series_from(closes)
        events = run_strategy(DonchianBreakout(5), s)
        kinds = [e.signal for e in events]
        self.assertEqual(kinds[0], Signal.LONG)
        self.assertIn(Signal.FLAT, kinds)
        self.assertTrue(all(k == Signal.LONG for k in kinds[:kinds.index(Signal.FLAT)]))

    def test_warmup_no_signal(self):
        s = series_from([10.0] * 4 + [100.0])
        self.assertEqual(run_strategy(DonchianBreakout(20), s), [])


class RsiReversionTest(unittest.TestCase):
    def test_oversold_recovery_enters(self):
        # 连续下跌把 RSI 压到 0，再连续上涨使其回升越过 30
        closes = [100.0 - i * 0.8 for i in range(25)]
        base = closes[-1]
        closes += [base + i * 1.2 for i in range(1, 25)]
        s = series_from(closes)
        events = run_strategy(RsiReversion(14, 30, 70), s)
        self.assertTrue(len(events) >= 1)
        self.assertEqual(events[0].signal, Signal.LONG)
        self.assertEqual([e.date for e in events], sorted({e.date for e in events}))

    def test_bad_params(self):
        with self.assertRaises(ValueError):
            RsiReversion(14, 80, 20)


class RunnerIoTest(unittest.TestCase):
    def test_symbol_mismatch_rejected(self):
        s = series_from([100.0] * 20)
        bad = [SignalEvent("OTHER", s[10].date, Signal.LONG, 1.0, "x")]
        strat = DonchianBreakout(5)
        strat.generate = lambda series: bad
        with self.assertRaises(ValueError):
            run_strategy(strat, s)

    def test_write_and_read_signals(self):
        s = series_from([10.0] * 12 + [20.0] + [20.0] * 6 + [5.0])
        events = run_strategy(DonchianBreakout(5), s)
        with tempfile.TemporaryDirectory() as d:
            path = write_signals(os.path.join(d, "sig.csv"), events)
            from riskforge.strategy.runner import read_signals
            rows = read_signals(path)
            self.assertEqual(len(rows), len(events))
            self.assertEqual(rows[0]["symbol"], "X")
            self.assertIn(rows[0]["signal"], {"long", "flat"})
            self.assertTrue(rows[0]["reason"])


if __name__ == "__main__":
    unittest.main()

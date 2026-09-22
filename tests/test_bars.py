import context  # noqa: F401
import unittest
from datetime import date

from riskforge.data.bars import Bar, BarSeries
from riskforge.types import Frequency


def _bar(d, close=100.0, symbol="X"):
    return Bar(symbol, d, close, close, close, close, 1000.0)


class BarsTest(unittest.TestCase):
    def test_append_order_and_dup(self):
        s = BarSeries("X")
        s.append(_bar(date(2024, 1, 2)))
        s.append(_bar(date(2024, 1, 3)))
        with self.assertRaises(ValueError):
            s.append(_bar(date(2024, 1, 3)))
        with self.assertRaises(ValueError):
            s.append(_bar(date(2024, 1, 1)))
        with self.assertRaises(ValueError):
            s.append(_bar(date(2024, 1, 4), symbol="Y"))

    def test_returns_and_total(self):
        s = BarSeries("X", [
            _bar(date(2024, 1, 2), 100.0),
            _bar(date(2024, 1, 3), 110.0),
            _bar(date(2024, 1, 4), 99.0),
        ])
        r = s.simple_returns(adjusted=False)
        self.assertEqual(len(r), 2)
        self.assertAlmostEqual(r[0], 0.10, places=12)
        self.assertAlmostEqual(r[1], 99.0 / 110.0 - 1, places=12)
        self.assertAlmostEqual(
            s.total_return(adjusted=False), 99.0 / 100.0 - 1, places=12
        )

    def test_slice_and_lookup(self):
        s = BarSeries("X", [_bar(date(2024, 1, d)) for d in range(2, 9)],
                      freq=Frequency.DAILY)
        self.assertEqual(len(s), 7)
        sub = s.between(date(2024, 1, 3), date(2024, 1, 5))
        self.assertEqual(
            sub.dates, [date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5)]
        )
        self.assertEqual(s.loc(date(2024, 1, 4)).close, 100.0)
        self.assertIsNone(s.get(date(2024, 2, 1)))
        self.assertEqual(s[0].date, date(2024, 1, 2))

    def test_invalid_ohlc_rejected(self):
        with self.assertRaises(ValueError):
            Bar("X", date(2024, 1, 2), 100, 90, 110, 100, 10)


if __name__ == "__main__":
    unittest.main()

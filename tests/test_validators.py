import context  # noqa: F401
import unittest
from datetime import date

from riskforge.data.bars import Bar
from riskforge.data.calendar import TradingCalendar
from riskforge.data.synthetic import GBMParams, generate_bars
from riskforge.data.validators import has_errors, validate_bars


def _bar(d, c, symbol="X"):
    return Bar(symbol, d, c, c, c, c, 1000.0)


class ValidatorsTest(unittest.TestCase):
    def setUp(self):
        self.cal = TradingCalendar()

    def test_clean_synthetic_passes(self):
        bars = generate_bars("X", date(2024, 1, 2), 60,
                             params=GBMParams(sigma=0.1), seed=3, calendar=self.cal)
        issues = validate_bars(bars, calendar=self.cal)
        self.assertFalse(has_errors(issues), [str(i) for i in issues])

    def test_empty(self):
        self.assertTrue(has_errors(validate_bars([])))

    def test_duplicate_date(self):
        bars = generate_bars("X", date(2024, 1, 2), 10, seed=1, calendar=self.cal)
        bad = list(bars) + [bars[5]]
        codes = {i.code for i in validate_bars(bad) if i.severity == "error"}
        self.assertIn("DUP_DATE", codes)

    def test_unsorted(self):
        bars = generate_bars("X", date(2024, 1, 2), 10, seed=1, calendar=self.cal)
        codes = {i.code for i in validate_bars(list(reversed(bars)))
                 if i.severity == "error"}
        self.assertIn("NOT_SORTED", codes)

    def test_mixed_symbol(self):
        bars = generate_bars("X", date(2024, 1, 2), 5, seed=1, calendar=self.cal)
        mixed = list(bars) + [_bar(date(2024, 1, 10), 1.0, symbol="Y")]
        codes = {i.code for i in validate_bars(mixed) if i.severity == "error"}
        self.assertIn("MIXED_SYMBOL", codes)

    def test_abnormal_jump_is_warning(self):
        bars = [_bar(date(2024, 1, 2), 100.0), _bar(date(2024, 1, 3), 200.0)]
        issues = validate_bars(bars, calendar=self.cal)
        self.assertFalse(has_errors(issues))
        self.assertIn("ABNORMAL_JUMP", {i.code for i in issues})

    def test_missing_session_is_warning(self):
        days = self.cal.trading_days(date(2024, 1, 2), date(2024, 1, 8))
        days = [d for d in days if d != date(2024, 1, 3)]  # 人为缺一天
        bars = [_bar(d, 100.0 + i) for i, d in enumerate(days)]
        issues = validate_bars(bars, calendar=self.cal)
        self.assertIn("MISSING_SESSION", {i.code for i in issues})
        self.assertFalse(has_errors(issues))


if __name__ == "__main__":
    unittest.main()

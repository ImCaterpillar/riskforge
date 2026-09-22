import context  # noqa: F401
import unittest
from datetime import date

from riskforge.data.calendar import TradingCalendar


class CalendarTest(unittest.TestCase):
    def setUp(self):
        # 2024-01-01 周一；用一个固定节假日
        self.cal = TradingCalendar(holidays={date(2024, 1, 1)})

    def test_weekend_and_holiday(self):
        self.assertTrue(self.cal.is_trading_day(date(2024, 1, 2)))   # 周二
        self.assertFalse(self.cal.is_trading_day(date(2024, 1, 6)))  # 周六
        self.assertFalse(self.cal.is_trading_day(date(2024, 1, 1)))  # 节假日

    def test_next_prev(self):
        self.assertEqual(self.cal.next_trading_day(date(2024, 1, 5)),
                         date(2024, 1, 8))   # 周五 -> 下周一
        self.assertEqual(self.cal.prev_trading_day(date(2024, 1, 8)),
                         date(2024, 1, 5))

    def test_range_count(self):
        days = self.cal.trading_days(date(2024, 1, 1), date(2024, 1, 7))
        # 周一节假日 + 周末两天 => 4 个交易日（周二到周五）
        self.assertEqual(len(days), 4)
        self.assertEqual(self.cal.count_sessions(date(2024, 1, 1), date(2024, 1, 7)), 4)

    def test_missing_sessions(self):
        # 实际只有周二、周四，缺周三（在首末之间）
        present = [date(2024, 1, 2), date(2024, 1, 4)]
        missing = self.cal.missing_sessions(present)
        self.assertEqual(missing, [date(2024, 1, 3)])

    def test_from_file(self):
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "h.txt")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("# 注释\n2024-01-01\n\n2024-02-12\n")
            cal = TradingCalendar.from_file(p)
            self.assertFalse(cal.is_trading_day(date(2024, 2, 12)))
            self.assertTrue(cal.is_trading_day(date(2024, 1, 2)))


if __name__ == "__main__":
    unittest.main()

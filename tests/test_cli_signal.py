import context  # noqa: F401
import csv
import os
import tempfile
import unittest
from datetime import date

from riskforge.cli import main
from riskforge.data.bars import Bar, BarSeries
from riskforge.data.calendar import TradingCalendar
from riskforge.data.feed import CsvFeed

CAL = TradingCalendar()
DATES = CAL.trading_days(date(2024, 1, 1), date(2024, 6, 30))


def _write_csv(directory, symbol, closes):
    bars = [Bar(symbol, d, float(c), float(c), float(c), float(c), 1000.0)
            for d, c in zip(DATES, closes)]
    feed = CsvFeed(directory)
    feed.write(symbol, BarSeries(symbol, bars))
    return os.path.join(directory, f"{symbol}.csv")


class CliSignalTest(unittest.TestCase):
    def setUp(self):
        # 横盘 -> 急涨 -> 急跌，确保 ma-cross 有信号
        self.closes = [100.0] * 30 + [100 + i * 3 for i in range(1, 15)] \
            + [140 - i * 3 for i in range(1, 15)]

    def test_generate_ma_cross(self):
        with tempfile.TemporaryDirectory() as d:
            csv_path = _write_csv(d, "DEMO", self.closes)
            out = os.path.join(d, "signals.csv")
            rc = main(["signal", "generate", "--file", csv_path,
                       "--strategy", "ma-cross", "--fast", "5", "--slow", "20",
                       "--out", out])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.isfile(out))
            with open(out, encoding="utf-8-sig", newline="") as fh:
                rows = list(csv.DictReader(fh))
            self.assertGreaterEqual(len(rows), 1)
            self.assertEqual(set(rows[0].keys()),
                             {"date", "symbol", "signal", "price", "reason"})
            self.assertTrue(all(r["signal"] in {"long", "flat"} for r in rows))
            self.assertTrue(all(r["symbol"] == "DEMO" for r in rows))

    def test_generate_donchian_default_out(self):
        with tempfile.TemporaryDirectory() as d:
            csv_path = _write_csv(d, "BETA", self.closes)
            rc = main(["signal", "generate", "--file", csv_path,
                       "--strategy", "donchian", "--window", "10"])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.isfile(
                os.path.join(d, "BETA.donchian.signals.csv")))

    def test_missing_file_rc2(self):
        rc = main(["signal", "generate", "--file", os.path.join("n", "x.csv")])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()

import context  # noqa: F401
import os
import tempfile
import unittest
from datetime import date

from riskforge.data.feed import CsvFeed
from riskforge.data.synthetic import GBMParams, generate_bars
from riskforge.data.bars import BarSeries
from riskforge.data.calendar import TradingCalendar


class CsvFeedTest(unittest.TestCase):
    def setUp(self):
        self.cal = TradingCalendar()
        self.bars = generate_bars(
            "DEMO", date(2024, 1, 2), 40,
            params=GBMParams(), seed=3, calendar=self.cal,
        )
        self.series = BarSeries("DEMO", self.bars)

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            feed = CsvFeed(d)
            path = feed.write("DEMO", self.series)
            self.assertTrue(os.path.isfile(path))
            self.assertEqual(feed.symbols(), ["DEMO"])
            loaded = feed.load("DEMO")
            self.assertEqual(len(loaded), len(self.series))
            self.assertEqual(loaded.dates, self.series.dates)
            for a, b in zip(loaded, self.series):
                self.assertAlmostEqual(a.open, b.open, places=6)
                self.assertAlmostEqual(a.close, b.close, places=6)
                self.assertAlmostEqual(a.volume, b.volume, places=2)

    def test_missing_column_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "BAD.csv"), "w", encoding="utf-8") as fh:
                fh.write("date,open,close\n2024-01-02,1,1\n")
            feed = CsvFeed(d)
            with self.assertRaises(ValueError):
                feed.load("BAD")

    def test_unsafe_symbol(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                CsvFeed(d).path_for("../escape")


if __name__ == "__main__":
    unittest.main()

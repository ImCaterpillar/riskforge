import context  # noqa: F401
import math
import unittest

from riskforge.indicators import (
    atr, bollinger, ema, macd, rolling_max, rolling_min, rolling_std, rsi, sma,
    true_ranges,
)


class SmaEmaTest(unittest.TestCase):
    def test_sma_known(self):
        self.assertEqual(sma([1, 2, 3, 4, 5], 3), [None, None, 2.0, 3.0, 4.0])

    def test_sma_window_too_large_all_none(self):
        self.assertEqual(sma([1, 2], 5), [None, None])

    def test_sma_bad_window_and_empty(self):
        with self.assertRaises(ValueError):
            sma([1, 2, 3], 0)
        with self.assertRaises(ValueError):
            sma([], 3)

    def test_ema_constant_is_constant(self):
        out = ema([42.0] * 10, 5)
        self.assertTrue(all(abs(v - 42.0) < 1e-12 for v in out))

    def test_ema_step_tracks(self):
        out = ema([10.0] * 5 + [20.0] * 20, 5)
        self.assertAlmostEqual(out[0], 10.0, places=12)
        self.assertGreater(out[-1], 15.0)
        self.assertLess(out[-1], 20.0)


class VolatilityTest(unittest.TestCase):
    def test_rolling_std_constant_zero(self):
        out = rolling_std([7.0] * 6, 3)
        self.assertEqual(out[:2], [None, None])
        self.assertTrue(all(abs(v) < 1e-12 for v in out[2:]))

    def test_rolling_std_known_population(self):
        out = rolling_std([1.0, 2.0, 3.0], 3, ddof=0)
        self.assertAlmostEqual(out[2], math.sqrt(2.0 / 3.0), places=12)

    def test_rolling_extrema(self):
        x = [3, 1, 4, 1, 5, 9, 2]
        self.assertEqual(rolling_max(x, 3)[-1], 9)
        self.assertEqual(rolling_min(x, 3)[3], 1)

    def test_bollinger_constant_bands_equal(self):
        mid, up, lo = bollinger([5.0] * 25, 20, 2.0)
        for i in range(19, 25):
            self.assertAlmostEqual(up[i], mid[i], places=12)
            self.assertAlmostEqual(lo[i], mid[i], places=12)

    def test_bollinger_order_and_mid(self):
        x = [10 + math.sin(i) * (1 + i / 10) for i in range(40)]
        mid, up, lo = bollinger(x, 20, 2.0)
        self.assertEqual(mid, sma(x, 20))
        for i in range(19, 40):
            self.assertGreaterEqual(up[i], mid[i])
            self.assertLessEqual(lo[i], mid[i])


class RsiMacdAtrTest(unittest.TestCase):
    def test_rsi_extremes_and_warmup(self):
        period = 14
        up = [100 + i for i in range(30)]
        down = [100 - i for i in range(30)]
        r_up = rsi(up, period)
        r_down = rsi(down, period)
        self.assertTrue(all(v is None for v in r_up[:period]))
        self.assertTrue(all(abs(v - 100.0) < 1e-9 for v in r_up[period:]))
        self.assertTrue(all(abs(v - 0.0) < 1e-9 for v in r_down[period:]))

    def test_rsi_bad_period(self):
        with self.assertRaises(ValueError):
            rsi([1, 2, 3], 0)

    def test_macd_uptrend_positive(self):
        close = [100 + 0.2 * i ** 1.5 for i in range(60)]
        dif, dea, hist = macd(close, 12, 26, 9)
        self.assertEqual(len(dif), len(dea), len(hist))
        self.assertTrue(all(v is None for v in dif[:25]))
        self.assertGreater(dif[-1], 0.0)

    def test_macd_bad_params(self):
        with self.assertRaises(ValueError):
            macd([1, 2, 3], fast=26, slow=12)

    def test_true_range_first(self):
        trs = true_ranges([11, 12], [9, 10], [10, 11])
        self.assertAlmostEqual(trs[0], 2.0, places=12)

    def test_atr_flat_zero_widening_positive(self):
        n = 20
        high = [10.0] * n
        low = [10.0] * n
        close = [10.0] * n
        out = atr(high, low, close, 14)
        self.assertTrue(all(abs(v) < 1e-12 for v in out[13:] if v is not None))
        # 让波幅逐日扩大
        for i in range(14, n):
            high[i] = 10.0 + (i - 13)
            low[i] = 10.0 - (i - 13)
        out2 = atr(high, low, close, 14)
        self.assertGreater(out2[-1], out2[13])


if __name__ == "__main__":
    unittest.main()

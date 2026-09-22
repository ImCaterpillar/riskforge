"""指标的纯函数实现。

只用标准库（``statistics`` / ``math``）。每个函数都返回与输入等长的列表，
预热位置为 ``None``，方便与 K 线按下标对齐。
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

Number = float


def _empty_check(x: Sequence[float]) -> None:
    if x is None or len(x) == 0:
        raise ValueError("指标输入序列不能为空")


def sma(x: Sequence[float], window: int) -> List[Optional[float]]:
    """简单移动平均；首个有效值在下标 ``window-1``。"""
    _empty_check(x)
    if window <= 0:
        raise ValueError("window 必须为正整数")
    out: List[Optional[float]] = [None] * len(x)
    if window > len(x):
        return out
    run = sum(x[:window])
    out[window - 1] = run / window
    for i in range(window, len(x)):
        run += x[i] - x[i - window]
        out[i] = run / window
    return out


def ema(x: Sequence[float], span: int) -> List[Optional[float]]:
    """指数移动平均，权重 ``alpha = 2/(span+1)``，以首个观测为种子。

    与很多库不同，这里不做 SMA 种子预热，从下标 0 起即有定义（首值=输入首值），
    语义简单、确定；需要预热的调用方自行截断前若干个值。
    """
    _empty_check(x)
    if span < 1:
        raise ValueError("span 必须 >= 1")
    alpha = 2.0 / (span + 1.0)
    out: List[Optional[float]] = [None] * len(x)
    prev = float(x[0])
    out[0] = prev
    for i in range(1, len(x)):
        prev = alpha * float(x[i]) + (1 - alpha) * prev
        out[i] = prev
    return out


def rolling_std(x: Sequence[float], window: int, ddof: int = 0) -> List[Optional[float]]:
    """滚动标准差（默认总体标准差 ddof=0），预热为 None。"""
    _empty_check(x)
    if window <= 1 and ddof == 1:
        raise ValueError("样本标准差要求 window>=2")
    if window <= 0:
        raise ValueError("window 必须为正整数")
    out: List[Optional[float]] = [None] * len(x)
    if window > len(x):
        return out
    for i in range(window - 1, len(x)):
        chunk = x[i - window + 1: i + 1]
        m = sum(chunk) / window
        var = sum((v - m) ** 2 for v in chunk) / (window - ddof)
        out[i] = math.sqrt(var)
    return out


def rolling_max(x: Sequence[float], window: int) -> List[Optional[float]]:
    """滚动窗口最大值（含当前 bar）。"""
    _empty_check(x)
    if window <= 0:
        raise ValueError("window 必须为正整数")
    out: List[Optional[float]] = [None] * len(x)
    for i in range(len(x)):
        lo = max(0, i - window + 1)
        out[i] = max(x[lo: i + 1])
    return out


def rolling_min(x: Sequence[float], window: int) -> List[Optional[float]]:
    """滚动窗口最小值（含当前 bar）。"""
    _empty_check(x)
    if window <= 0:
        raise ValueError("window 必须为正整数")
    out: List[Optional[float]] = [None] * len(x)
    for i in range(len(x)):
        lo = max(0, i - window + 1)
        out[i] = min(x[lo: i + 1])
    return out


def bollinger(
    x: Sequence[float], window: int = 20, n_std: float = 2.0, ddof: int = 0
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """布林带，返回 (中轨 SMA, 上轨, 下轨)。常数序列带宽为 0。"""
    mid = sma(x, window)
    sd = rolling_std(x, window, ddof=ddof)
    upper: List[Optional[float]] = [None] * len(x)
    lower: List[Optional[float]] = [None] * len(x)
    for i in range(len(x)):
        if mid[i] is not None and sd[i] is not None:
            upper[i] = mid[i] + n_std * sd[i]
            lower[i] = mid[i] - n_std * sd[i]
    return mid, upper, lower


def rsi(close: Sequence[float], period: int = 14) -> List[Optional[float]]:
    """Wilder RSI。首个有效值在下标 ``period``（需要 period 个涨跌幅）。"""
    _empty_check(close)
    if period < 1:
        raise ValueError("period 必须 >= 1")
    n = len(close)
    out: List[Optional[float]] = [None] * n
    if n <= period:
        return out
    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        ch = close[i] - close[i - 1]
        if ch >= 0:
            gains += ch
        else:
            losses -= ch
    avg_gain = gains / period
    avg_loss = losses / period
    out[period] = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    for i in range(period + 1, n):
        ch = close[i] - close[i - 1]
        gain = max(ch, 0.0)
        loss = max(-ch, 0.0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        out[i] = 100.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    return out


def macd(
    close: Sequence[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """MACD，返回 (DIF 快线, DEA 信号线, 柱)。

    DIF/DEA 在慢线预热完成（下标 ``slow-1``）前为 None；DEA 还需 ``signal`` 个 DIF。
    """
    if not (0 < fast < slow):
        raise ValueError("要求 0 < fast < slow")
    if signal < 1:
        raise ValueError("signal 必须 >= 1")
    n = len(close)
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    dif: List[Optional[float]] = [None] * n
    for i in range(slow - 1, n):
        dif[i] = ema_fast[i] - ema_slow[i]
    # DEA = 对有效 DIF 再做 EMA
    dea: List[Optional[float]] = [None] * n
    hist: List[Optional[float]] = [None] * n
    valid_idx = [i for i in range(n) if dif[i] is not None]
    if len(valid_idx) >= signal:
        first = valid_idx[0]
        alpha = 2.0 / (signal + 1.0)
        prev = dif[first]
        dea[first] = prev
        hist[first] = (dif[first] - prev) * 2.0
        for i in valid_idx[1:]:
            prev = alpha * dif[i] + (1 - alpha) * prev
            dea[i] = prev
            hist[i] = (dif[i] - prev) * 2.0
    return dif, dea, hist


def true_ranges(
    high: Sequence[float], low: Sequence[float], close: Sequence[float]
) -> List[float]:
    """真实波幅 TR；首根没有前收，TR=high-low。要求三个序列等长。"""
    if not (len(high) == len(low) == len(close)) or len(high) == 0:
        raise ValueError("high/low/close 必须等长且非空")
    trs: List[float] = [high[0] - low[0]]
    for i in range(1, len(close)):
        pc = close[i - 1]
        trs.append(max(high[i] - low[i], abs(high[i] - pc), abs(low[i] - pc)))
    return trs


def atr(
    high: Sequence[float],
    low: Sequence[float],
    close: Sequence[float],
    period: int = 14,
) -> List[Optional[float]]:
    """Wilder ATR；首个有效值在下标 ``period-1``。"""
    if period < 1:
        raise ValueError("period 必须 >= 1")
    trs = true_ranges(high, low, close)
    n = len(trs)
    out: List[Optional[float]] = [None] * n
    if n < period:
        return out
    run = sum(trs[:period])
    out[period - 1] = run / period
    for i in range(period, n):
        run = (out[i - 1] * (period - 1) + trs[i]) / period
        out[i] = run
    return out

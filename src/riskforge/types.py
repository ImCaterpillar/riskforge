"""跨模块共用的基础枚举与轻量类型。"""
from __future__ import annotations

from enum import Enum


class Frequency(str, Enum):
    """K 线频率。字符串值用于序列化与命令行参数。"""

    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1mo"


class Side(str, Enum):
    """交易方向。"""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """订单类型。"""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderStatus(str, Enum):
    """订单生命周期状态。"""

    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Signal(str, Enum):
    """策略信号（M2 使用，提前定义以稳定接口）。"""

    LONG = "long"
    FLAT = "flat"
    SHORT = "short"

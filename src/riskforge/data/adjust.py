"""拆股 / 分红的后复权处理。

后复权因子 ``adj_factor`` 让**复权收盘价的逐期收益等于含拆股、现金分红再投的总收益**，
从而在除权日不会出现人为的价格跳空。约定：

- 拆股：``ratio`` 为每股老股拆成的新股数（2:1 拆股记 2.0）；除权日前的价格除以 ratio；
- 现金分红：每股派现 ``cash``，除权日前价格乘 ``(P_prev - cash) / P_prev``，
  其中 ``P_prev`` 为除权日前一交易日的（未复权）收盘价。

因子对**晚于**该 bar 的全部公司行为累乘；最新 bar 的因子为 1.0。
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from typing import Dict, Iterable, List, Sequence

from riskforge.data.bars import Bar


@dataclass(frozen=True, slots=True)
class CorporateAction:
    """一次公司行为。"""

    ex_date: date
    """除权除息日。"""
    kind: str
    """``"split"`` 或 ``"dividend"``。"""
    value: float
    """split=拆股比例（新/老）；dividend=每股现金分红。"""

    def __post_init__(self) -> None:
        if self.kind not in ("split", "dividend"):
            raise ValueError(f"未知公司行为类型：{self.kind!r}")
        if self.value <= 0:
            raise ValueError("公司行为数值必须为正")
        if self.kind == "dividend" and self.value <= 0:
            raise ValueError("分红金额必须为正")


def _prev_bar_close(bars: Sequence[Bar], ex_date: date) -> float:
    """取严格早于 ex_date 的最近一根 bar 的未复权收盘价。"""
    prev: Bar | None = None
    for bar in bars:
        if bar.date < ex_date:
            prev = bar
        else:
            break
    if prev is None:
        raise ValueError(f"除权日 {ex_date} 之前没有行情，无法计算复权因子")
    return prev.close


def compute_factors(bars: Sequence[Bar], actions: Iterable[CorporateAction]) -> Dict[date, float]:
    """为每根 bar 计算后复权因子（{date: factor}）。"""
    ordered = sorted(bars, key=lambda b: b.date)
    if not ordered:
        return {}
    acts = sorted(actions, key=lambda a: a.ex_date)

    # 每个除权日，对"早于除权日"的 bar 施加的乘数
    event_mult: Dict[date, float] = {}
    for a in acts:
        if a.kind == "split":
            if a.value <= 0:
                raise ValueError("拆股比例必须为正")
            event_mult[a.ex_date] = 1.0 / a.value
        else:
            p_prev = _prev_bar_close(ordered, a.ex_date)
            if a.value >= p_prev:
                raise ValueError(
                    f"分红 {a.value} 不小于除权前收盘 {p_prev}，数据可能有误"
                )
            event_mult[a.ex_date] = (p_prev - a.value) / p_prev

    factors: Dict[date, float] = {}
    for bar in ordered:
        factor = 1.0
        for ex_date, mult in event_mult.items():
            if bar.date < ex_date:  # 仅作用于除权日之前
                factor *= mult
        factors[bar.date] = factor
    return factors


def apply_actions(bars: Sequence[Bar], actions: Iterable[CorporateAction]) -> List[Bar]:
    """返回带复权因子的新 bar 列表（不修改入参）。"""
    factors = compute_factors(bars, actions)
    return [replace(b, adj_factor=factors[b.date]) for b in sorted(bars, key=lambda x: x.date)]

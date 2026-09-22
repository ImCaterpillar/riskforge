"""riskforge 命令行（M1 提供 data 子命令；回测/报告子命令随后续里程碑加入）。

示例：

    python -m riskforge data synth --out data/samples --days 126 --seed 7 \
        --symbol DEMO --symbol BETA,50,0.05,0.35
    python -m riskforge data validate --file data/samples/DEMO.csv
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from typing import Dict, List, Tuple

from riskforge import __version__
from riskforge.data.calendar import TradingCalendar
from riskforge.data.feed import CsvFeed
from riskforge.data.synthetic import GBMParams
from riskforge.data.validators import has_errors, validate_bars
from riskforge.strategy import (
    DonchianBreakout,
    MovingAverageCross,
    RsiReversion,
    run_strategy,
    write_signals,
)


def _parse_symbol_spec(text: str) -> Tuple[str, GBMParams]:
    """解析 ``NAME`` 或 ``NAME,s0,mu,sigma``。"""
    parts = [p.strip() for p in text.split(",")]
    name = parts[0]
    if not name:
        raise ValueError("标的代码为空")
    if len(parts) == 1:
        return name, GBMParams()
    if len(parts) != 4:
        raise ValueError(
            f"标的规格 {text!r} 格式应为 NAME 或 NAME,s0,mu,sigma"
        )
    return name, GBMParams(
        s0=float(parts[1]), mu=float(parts[2]), sigma=float(parts[3])
    )


def _cmd_synth(args: argparse.Namespace) -> int:
    spec: Dict[str, GBMParams] = {}
    for raw in args.symbol:
        name, params = _parse_symbol_spec(raw)
        spec[name] = params
    if not spec:
        spec = {"DEMO": GBMParams()}

    feed = CsvFeed(args.out)
    cal = TradingCalendar()
    # 延迟导入，避免仅校验时也依赖合成模块
    from riskforge.data.synthetic import generate_panel

    panel = generate_panel(spec, args.start, args.days, seed=args.seed, calendar=cal)
    for name in sorted(panel):
        from riskforge.data.bars import BarSeries

        series = BarSeries(name, panel[name])
        path = feed.write(name, series)
        print(f"已生成 {name}: {len(series)} 根日K -> {path}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    if not os.path.isfile(args.file):
        print(f"找不到文件：{args.file}", file=sys.stderr)
        return 2
    root = os.path.dirname(os.path.abspath(args.file))
    stem = os.path.splitext(os.path.basename(args.file))[0]
    try:
        series = CsvFeed(root).load(stem)
    except (ValueError, OSError) as exc:
        print(f"读取失败：{exc}", file=sys.stderr)
        return 2

    issues = validate_bars(list(series), calendar=TradingCalendar())
    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]
    for issue in issues:
        print(str(issue))
    print(
        f"{stem}: {len(series)} 根K线，{len(errors)} 个错误，{len(warnings)} 个警告"
    )
    if has_errors(issues):
        return 1
    print("校验通过（无硬错误）。")
    return 0


def _build_strategy(args: argparse.Namespace):
    if args.strategy == "ma-cross":
        return MovingAverageCross(fast=args.fast, slow=args.slow)
    if args.strategy == "donchian":
        return DonchianBreakout(window=args.window)
    if args.strategy == "rsi-reversion":
        return RsiReversion(period=args.rsi_period,
                            oversold=args.oversold, overbought=args.overbought)
    raise ValueError(f"未知策略：{args.strategy}")


def _cmd_signal(args: argparse.Namespace) -> int:
    if not os.path.isfile(args.file):
        print(f"找不到文件：{args.file}", file=sys.stderr)
        return 2
    root = os.path.dirname(os.path.abspath(args.file))
    stem = os.path.splitext(os.path.basename(args.file))[0]
    try:
        series = CsvFeed(root).load(stem)
        strategy = _build_strategy(args)
        events = run_strategy(strategy, series)
    except (ValueError, KeyError, OSError) as exc:
        print(f"生成信号失败：{exc}", file=sys.stderr)
        return 2

    out = args.out or os.path.join(root, f"{stem}.{args.strategy}.signals.csv")
    write_signals(out, events)
    longs = sum(1 for e in events if e.signal.value == "long")
    flats = sum(1 for e in events if e.signal.value == "flat")
    print(f"策略 {strategy.describe()}：{len(series)} 根K线，"
          f"信号 {len(events)} 个（入场 {longs} / 离场 {flats}）")
    for ev in events[-6:]:
        print(f"  {ev.date} {ev.signal.value:>4} @ {ev.price:.4f}  {ev.reason}")
    print(f"已写出：{out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="riskforge", description="事件驱动量化回测与风险分析框架")
    parser.add_argument("--version", action="version", version=f"riskforge {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    data = sub.add_parser("data", help="市场数据：合成 / 校验")
    data_sub = data.add_subparsers(dest="data_command", required=True)

    synth = data_sub.add_parser("synth", help="生成可复现的合成日K CSV（离线演示/测试）")
    synth.add_argument("--out", default="data/samples", help="输出目录")
    synth.add_argument("--start", type=date.fromisoformat,
                       default=date(2024, 1, 2), help="起始交易日 YYYY-MM-DD")
    synth.add_argument("--days", type=int, default=126, help="交易日数量")
    synth.add_argument("--seed", type=int, default=7, help="随机种子（固定即可复现）")
    synth.add_argument("--symbol", action="append", default=[],
                       help="标的，可重复；格式 NAME 或 NAME,s0,mu,sigma")
    synth.set_defaults(func=_cmd_synth)

    val = data_sub.add_parser("validate", help="校验一个日K CSV")
    val.add_argument("--file", required=True, help="CSV 文件路径")
    val.set_defaults(func=_cmd_validate)

    signal = sub.add_parser("signal", help="策略信号")
    signal_sub = signal.add_subparsers(dest="signal_command", required=True)
    gen = signal_sub.add_parser("generate", help="对一个日K CSV 生成交易信号 CSV")
    gen.add_argument("--file", required=True, help="日K CSV 文件路径")
    gen.add_argument("--strategy", choices=["ma-cross", "donchian", "rsi-reversion"],
                     default="ma-cross")
    gen.add_argument("--fast", type=int, default=10, help="ma-cross 快线窗口")
    gen.add_argument("--slow", type=int, default=30, help="ma-cross 慢线窗口")
    gen.add_argument("--window", type=int, default=20, help="donchian 通道窗口")
    gen.add_argument("--rsi-period", type=int, default=14)
    gen.add_argument("--oversold", type=float, default=30.0)
    gen.add_argument("--overbought", type=float, default=70.0)
    gen.add_argument("--out", default=None, help="输出信号 CSV 路径")
    gen.set_defaults(func=_cmd_signal)
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ValueError as exc:  # 参数语义错误
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

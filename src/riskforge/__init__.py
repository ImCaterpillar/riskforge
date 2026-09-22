"""riskforge —— 事件驱动量化回测与风险分析框架。

模块布局（按里程碑演进）：

- ``riskforge.data``     市场数据层：K 线、交易日历、数据源、复权、校验（M1）
- ``riskforge.strategy`` 策略与信号（M2，规划中）
- ``riskforge.engine``   事件驱动回测引擎：撮合、订单、费用滑点（M3，规划中）
- ``riskforge.risk``     绩效与风险指标（M4，规划中）
- ``riskforge.opt``      参数寻优与稳健性（M5，规划中）
- ``riskforge.report``   报告与可视化（M6，规划中）

核心设计原则：

1. 运行时仅依赖 Python 标准库，保证离线可构建、可测试、结果可复现；
2. 所有随机过程（合成行情、抽样）必须可通过 seed 复现；
3. 数据进入引擎前必须经过 :mod:`riskforge.data.validators` 校验。
"""

__version__ = "0.2.0"

__all__ = ["__version__"]

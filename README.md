# riskforge

[![CI](https://github.com/ImCaterpillar/riskforge/actions/workflows/ci.yml/badge.svg)](https://github.com/ImCaterpillar/riskforge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

事件驱动的**量化回测与风险分析框架**（Python）。面向个人研究：从行情数据、策略信号、
事件驱动撮合，到绩效与风险指标、参数稳健性、报告输出，提供一条可复现、可离线运行的完整链路。

> 状态：**M1 市场数据层、M2 指标与策略接口已完成并测试通过**；回测引擎/风险/寻优/报告按 `docs/roadmap.md` 持续开发。
> 本仓库为原创工程，以 MIT 协议开源；正常使用 AI 辅助编码，提交历史为真实开发过程，不回填、不伪造。

## 设计原则

1. **核心零第三方依赖**：数据层、引擎、风险指标、CLI、单元测试只用 Python 3.10+ 标准库，
   保证在隔离/无网络环境也能安装、运行、测试；图表等可选功能才依赖 matplotlib。
2. **可复现**：所有随机过程（合成行情、抽样）必须显式传 `seed`；相同输入产出相同结果。
3. **数据先校验后入引擎**：任何行情进入回测前都经过 OHLC 关系、日期单调性、缺口、复权等校验。
4. **收益口径一致**：拆股/现金分红通过后复权因子处理，复权收益等于含权总收益，除权日不产生人为跳空。

## 目录结构

```
riskforge/
├── pyproject.toml / requirements.txt   # 打包与依赖（核心 dependencies 为空）
├── src/riskforge/
│   ├── types.py                        # 频率/方向/订单类型/信号等枚举
│   ├── cli.py / __main__.py            # 命令行
│   ├── indicators/                     # M2 指标（SMA/EMA/布林/RSI/MACD/ATR）
│   ├── strategy/                       # M2 策略信号（均线/突破/RSI 回归）
│   └── data/                           # M1 市场数据层
│       ├── bars.py                     # Bar / BarSeries（收益、切片、复权价）
│       ├── calendar.py                 # 交易日历（周掩码+节假日）
│       ├── synthetic.py                # 可复现 GBM 合成行情
│       ├── feed.py                     # CsvFeed / SyntheticFeed
│       ├── adjust.py                   # 拆股/分红后复权
│       └── validators.py               # 入库前校验
├── tests/                              # 标准库 unittest，离线可跑
├── examples/                           # 可运行示例
└── data/samples/                       # 提交的小型合成样例数据（非真实标的）
```

## 安装与测试（离线）

核心无需安装任何第三方包。直接跑测试：

```bash
python -m unittest discover -s tests
```

或以可编辑方式安装（需要联网获取 setuptools，通常环境已自带）：

```bash
pip install -e .
```

安装后会提供 `riskforge` 命令行入口（与 `python -m riskforge` 等价）：

```bash
riskforge --version
```

推送或发起 PR 时，`.github/workflows/ci.yml` 会在 Python 3.11 / 3.12 上执行
`pip install -e .`、`python -m unittest discover -s tests`，并验证核心运行时依赖仍为空。

## 命令行用法

生成可复现的合成日 K（离线演示/测试用，**非真实标的**）：

```bash
python -m riskforge data synth --out data/samples --days 126 --seed 7 \
    --symbol DEMO --symbol BETA,50,0.05,0.35
# --symbol 写法：NAME  或  NAME,期初价,年化漂移,年化波动
```

校验一个日 K CSV（有硬错误时退出码为 1）：

```bash
python -m riskforge data validate --file data/samples/DEMO.csv
```

基于日 K 生成策略信号 CSV（`date,symbol,signal,price,reason`）：

```bash
python -m riskforge signal generate --file data/samples/DEMO.csv \
    --strategy ma-cross --fast 10 --slow 30 --out data/samples/DEMO.signals.csv
# --strategy 可选 ma-cross / donchian / rsi-reversion
```

一键复现样例上三种策略的信号：`python examples/run_signals.py`。

查看版本：`python -m riskforge --version`。

## 合成数据声明

`data/samples/` 与 `synthetic` 模块产出的是几何布朗运动假数据，仅用于离线测试、CI 与文档演示，
不代表任何真实证券，也不构成投资建议。接入真实行情请实现自己的 `DataFeed`，并先通过数据校验。

## 安全

- 仓库不得提交任何令牌、私钥、客户数据、内网地址；`.gitignore` 已排除常见密钥与本地数据目录。
- 真实数据与凭据放在仓库外或 `data/private/`（已忽略）。

## 许可证

基于 [MIT License](LICENSE) 开源，可自由使用、修改与分发，请保留版权声明。

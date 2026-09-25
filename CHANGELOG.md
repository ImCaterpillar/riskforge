# Changelog

本项目采用语义化版本，按真实开发里程碑记录。

## 未发版 —— 工程质量修复（2026-09-25）

### 修复
- `pyproject.toml` 的 `version` 由 `0.1.0` 更正为 `0.2.0`：该字段未随 0.2.0 里程碑同步，
  导致安装元数据（`pip show riskforge`）与 `riskforge --version`（读取 `__init__.__version__`）不一致。
- `pyproject.toml` 的 `license` 由 `Proprietary` 更正为 `MIT`，与仓库根 `LICENSE` 及
  README 的“基于 MIT 协议开源”保持一致。
- 删除 `src/riskforge/data/synthetic.py` 中未使用的 `typing.Sequence` 导入。

### 工程
- 新增 GitHub Actions CI（`.github/workflows/ci.yml`）：ubuntu-latest × Python 3.11/3.12，
  依次执行 `pip install -e .`、校验命令行入口、断言核心运行时依赖仍为空、
  `python -m unittest discover -s tests -v`、CLI 端到端 smoke（synth / validate / signal）。
- README 增加 CI 与 License 徽章，并补充命令行入口与 CI 说明。
- 复核确认：59 个标准库 unittest 全绿；`examples/` 两个脚本可运行，且重跑后提交的
  `data/samples/*.csv` 字节不变，固定 seed 的可复现性成立。

## 0.2.0 —— M2 指标与策略接口（2026-09-21）

### 新增
- 指标库 `riskforge.indicators`（纯函数、等长对齐、预热期为 None）：SMA、EMA、滚动标准差/极值、
  布林带、Wilder RSI、MACD（DIF/DEA/柱）、真实波幅 TR 与 Wilder ATR。
- 策略层 `riskforge.strategy`：`SignalEvent`、`Strategy` 抽象基类、`run_strategy` 结果校验
  （日期严格递增、同日不重复、标的一致）与信号 CSV 读写。
- 三个可运行策略：双均线金叉/死叉 `MovingAverageCross`、唐奇安通道突破 `DonchianBreakout`
  （回看窗口不含当前 bar，避免未来函数）、RSI 超卖回升 `RsiReversion`，均为 long-only。
- CLI：`python -m riskforge signal generate --file ... --strategy ma-cross|donchian|rsi-reversion`，
  输出 `date,symbol,signal,price,reason` 信号 CSV，并打印信号统计。
- 示例 `examples/run_signals.py`，对合成样例复现三种策略信号并落盘到 `data/samples/`。
- 新增 28 个标准库 unittest 用例，累计 59 个全绿。

## 0.1.0 —— M1 市场数据层（2026-09-21）

### 新增
- 市场数据模型 `Bar` / `BarSeries`：OHLC 不变量校验、复权价、简单/对数收益、区间切片。
- `TradingCalendar`：周掩码 + 节假日的交易日历，支持前后推交易日、区间枚举、缺口检测，可从文件加载节假日。
- 可复现合成行情 `synthetic`：GBM 收盘价、隔夜跳空、日内振幅与量能，固定 seed 完全确定；支持多标的面板。
- 数据源 `CsvFeed` / `SyntheticFeed`：每标的一个 CSV 的读写（含字段缺失检查、路径安全）与离线合成源。
- 公司行为复权 `adjust`：拆股与现金分红的后复权因子，保证复权收益在除权日连续。
- 数据校验 `validators`：OHLC 关系、日期单调/重复、多标的混入、异常跳空、交易日缺口，分级 error/warning。
- CLI：`python -m riskforge data synth|validate`，退出码区分通过/校验错误/用法错误。
- 31 个标准库 unittest 单测，离线全绿；提交 `data/samples` 合成样例。

### 工程
- 核心运行时零第三方依赖（仅 Python 3.10+ 标准库），保证离线可构建、可测试、可复现。

## 0.0.1 —— M0 工程骨架（2026-09-21）

- 建立 src 布局包结构、`pyproject.toml`、依赖策略（核心零依赖）、LICENSE（私有专有）、`.gitignore`。

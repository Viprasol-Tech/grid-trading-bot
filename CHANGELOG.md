# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[SemVer](https://semver.org/).

## [0.2.0] - 2025

### Added
- Geometric (log-spaced) grid spacing via `GridSpacing`, alongside the existing arithmetic grid.
- Take-profit and stop-loss bounds that liquidate inventory once and halt the grid on a breakout.
- Trailing grid that slides the ladder up to re-center on an upside breakout.
- `metrics` module with `returns`, `max_drawdown`, `sharpe_ratio`, and `cagr`.
- Enriched `BacktestResult` report: `num_buys`/`num_sells`, `total_fees`, `max_drawdown_pct`, `sharpe()`, and `cagr_pct()`.
- `BotConfig` — a validated, JSON-serialisable run configuration with `build_strategy()` / `build_exchange()` helpers.
- CLI subcommands: `backtest` (run from a JSON config, optionally on a price CSV) and `init-config`; `demo` gains a `--spacing` option and a rich report table.
- `numpy` dependency for vectorised metrics.

### Changed
- Roughly tripled the test suite (18 → 60 cases) covering geometric grids, risk controls, metrics, config, and the CLI.

## [0.1.0] - 2025

### Added
- Initial release of grid-trading-bot: Grid trading bot with a configurable price grid, simulated exchange, and backtest.

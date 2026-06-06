"""Tests for the enriched backtest report metrics."""

from __future__ import annotations

import math

from grid_trading_bot.backtest import run_backtest
from grid_trading_bot.cli import synthetic_prices
from grid_trading_bot.exchange import SimulatedExchange
from grid_trading_bot.grid import GridStrategy


def _run() -> object:
    prices = synthetic_prices()
    ex = SimulatedExchange(balances={"USDT": 10_000.0}, fee_rate=0.001)
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0)
    return run_backtest("BTC/USDT", prices, strat, ex)


def test_buy_sell_counts_sum_to_total() -> None:
    result = _run()
    assert result.num_buys + result.num_sells == result.num_fills  # type: ignore[attr-defined]
    assert result.num_buys > 0  # type: ignore[attr-defined]


def test_total_fees_non_negative_and_consistent() -> None:
    result = _run()
    assert result.total_fees >= 0.0  # type: ignore[attr-defined]
    assert math.isclose(  # type: ignore[attr-defined]
        result.total_fees, sum(f.fee for f in result.fills)
    )


def test_drawdown_is_a_percentage() -> None:
    result = _run()
    assert 0.0 <= result.max_drawdown_pct <= 100.0  # type: ignore[attr-defined]


def test_sharpe_and_cagr_are_finite() -> None:
    result = _run()
    assert math.isfinite(result.sharpe())  # type: ignore[attr-defined]
    assert math.isfinite(result.cagr_pct())  # type: ignore[attr-defined]


def test_flat_market_has_zero_drawdown() -> None:
    ex = SimulatedExchange(balances={"USDT": 1_000.0}, fee_rate=0.0)
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0)
    result = run_backtest("BTC/USDT", [100.0] * 20, strat, ex)
    assert result.max_drawdown_pct == 0.0
    assert result.total_fees == 0.0

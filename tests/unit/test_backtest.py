"""Tests for the backtest runner and its equity curve."""

from __future__ import annotations

import math

import pytest

from grid_trading_bot.backtest import run_backtest
from grid_trading_bot.cli import synthetic_prices
from grid_trading_bot.exchange import SimulatedExchange
from grid_trading_bot.grid import GridStrategy


def test_backtest_produces_equity_curve_and_fills() -> None:
    prices = synthetic_prices()
    ex = SimulatedExchange(balances={"USDT": 10_000.0}, fee_rate=0.001)
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0)
    result = run_backtest("BTC/USDT", prices, strat, ex)

    assert len(result.equity_curve) == len(prices)
    assert result.num_fills > 0
    assert math.isclose(result.final_equity, result.equity_curve[-1])
    assert math.isclose(result.pnl, result.final_equity - result.starting_equity)


def test_backtest_no_trades_preserves_equity() -> None:
    # A flat price never crosses a grid line, so no fills and equity is unchanged.
    prices = [100.0] * 10
    ex = SimulatedExchange(balances={"USDT": 1_000.0}, fee_rate=0.001)
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0)
    result = run_backtest("BTC/USDT", prices, strat, ex)

    assert result.num_fills == 0
    assert math.isclose(result.final_equity, 1_000.0)
    assert math.isclose(result.return_pct, 0.0)


def test_backtest_empty_prices_raises() -> None:
    ex = SimulatedExchange(balances={"USDT": 1_000.0})
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0)
    with pytest.raises(ValueError):
        run_backtest("BTC/USDT", [], strat, ex)

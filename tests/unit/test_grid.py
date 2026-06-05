"""Tests for grid level math, buy/sell behaviour, and validation."""

from __future__ import annotations

import math

import pytest

from grid_trading_bot.exchange import SimulatedExchange
from grid_trading_bot.grid import GridStrategy
from grid_trading_bot.models import Side


def test_grid_lines_are_evenly_spaced() -> None:
    strat = GridStrategy(lower=100.0, upper=200.0, levels=5, quantity=1.0)
    assert strat.grid_lines() == [100.0, 125.0, 150.0, 175.0, 200.0]
    assert math.isclose(strat.step, 25.0)


@pytest.mark.parametrize(
    ("lower", "upper", "levels", "quantity"),
    [
        (0.0, 100.0, 5, 1.0),  # lower not > 0
        (100.0, 50.0, 5, 1.0),  # upper <= lower
        (100.0, 100.0, 5, 1.0),  # upper == lower
        (50.0, 100.0, 1, 1.0),  # levels < 2
        (50.0, 100.0, 5, 0.0),  # quantity not > 0
    ],
)
def test_invalid_params_raise_value_error(
    lower: float, upper: float, levels: int, quantity: float
) -> None:
    with pytest.raises(ValueError):
        GridStrategy(lower=lower, upper=upper, levels=levels, quantity=quantity)


def test_buys_on_dip() -> None:
    ex = SimulatedExchange(balances={"USDT": 10_000.0}, fee_rate=0.0)
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0)
    strat.on_price("BTC/USDT", 100.0, ex)  # establish starting grid index
    orders = strat.on_price("BTC/USDT", 90.0, ex)  # price fell through levels
    assert len(orders) == 1
    assert orders[0].side is Side.BUY


def test_sells_on_rise_when_holding_base() -> None:
    ex = SimulatedExchange(balances={"USDT": 10_000.0, "BTC": 5.0}, fee_rate=0.0)
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0)
    strat.on_price("BTC/USDT", 100.0, ex)
    orders = strat.on_price("BTC/USDT", 110.0, ex)  # price rose through levels
    assert len(orders) == 1
    assert orders[0].side is Side.SELL


def test_no_sell_without_base_balance() -> None:
    ex = SimulatedExchange(balances={"USDT": 10_000.0}, fee_rate=0.0)
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0)
    strat.on_price("BTC/USDT", 100.0, ex)
    orders = strat.on_price("BTC/USDT", 110.0, ex)  # would sell, but no BTC held
    assert orders == []


def test_first_tick_emits_no_orders() -> None:
    ex = SimulatedExchange(balances={"USDT": 10_000.0}, fee_rate=0.0)
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0)
    assert strat.on_price("BTC/USDT", 100.0, ex) == []

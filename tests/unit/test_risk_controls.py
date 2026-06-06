"""Tests for take-profit, stop-loss, and trailing-grid risk controls."""

from __future__ import annotations

import math

import pytest

from grid_trading_bot.exchange import SimulatedExchange
from grid_trading_bot.grid import GridStrategy
from grid_trading_bot.models import Side


def test_take_profit_liquidates_inventory_and_stops() -> None:
    ex = SimulatedExchange(balances={"USDT": 10_000.0, "BTC": 3.0}, fee_rate=0.0)
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0, take_profit=120.0)
    strat.on_price("BTC/USDT", 100.0, ex)
    orders = strat.on_price("BTC/USDT", 121.0, ex)
    assert len(orders) == 1
    assert orders[0].side is Side.SELL
    assert math.isclose(orders[0].quantity, 3.0)  # full inventory
    assert strat.stopped
    # Once stopped, no further orders even if price dips.
    assert strat.on_price("BTC/USDT", 90.0, ex) == []


def test_stop_loss_liquidates_inventory_and_stops() -> None:
    ex = SimulatedExchange(balances={"USDT": 1_000.0, "BTC": 2.0}, fee_rate=0.0)
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0, stop_loss=80.0)
    strat.on_price("BTC/USDT", 100.0, ex)
    orders = strat.on_price("BTC/USDT", 79.0, ex)
    assert len(orders) == 1
    assert orders[0].side is Side.SELL
    assert math.isclose(orders[0].quantity, 2.0)
    assert strat.stopped


def test_stop_with_no_inventory_just_stops() -> None:
    ex = SimulatedExchange(balances={"USDT": 1_000.0}, fee_rate=0.0)
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0, stop_loss=80.0)
    strat.on_price("BTC/USDT", 100.0, ex)
    assert strat.on_price("BTC/USDT", 70.0, ex) == []
    assert strat.stopped


def test_trailing_grid_slides_up_on_breakout() -> None:
    ex = SimulatedExchange(balances={"USDT": 10_000.0, "BTC": 5.0}, fee_rate=0.0)
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0, trailing=True)
    strat.on_price("BTC/USDT", 100.0, ex)
    strat.on_price("BTC/USDT", 130.0, ex)  # break above upper -> slide
    assert math.isclose(strat.upper, 130.0)
    assert math.isclose(strat.lower, 100.0)  # width 30 preserved
    assert not strat.stopped


def test_trailing_does_not_stop_at_top() -> None:
    ex = SimulatedExchange(balances={"USDT": 10_000.0, "BTC": 5.0}, fee_rate=0.0)
    strat = GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0, trailing=True)
    strat.on_price("BTC/USDT", 100.0, ex)
    # After sliding, a further rise keeps trading rather than selling everything.
    strat.on_price("BTC/USDT", 130.0, ex)
    assert strat.upper > 115.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"take_profit": -1.0},
        {"stop_loss": 0.0},
        {"trailing": True, "take_profit": 200.0},
    ],
)
def test_invalid_risk_params_raise(kwargs: dict[str, float | bool]) -> None:
    with pytest.raises(ValueError):
        GridStrategy(lower=85.0, upper=115.0, levels=13, quantity=1.0, **kwargs)  # type: ignore[arg-type]

"""Tests for the simulated exchange balance and fee accounting."""

from __future__ import annotations

import math

import pytest

from grid_trading_bot.exchange import SimulatedExchange
from grid_trading_bot.models import Order, Side


def test_buy_updates_balances_without_fee() -> None:
    ex = SimulatedExchange(balances={"USDT": 1_000.0}, fee_rate=0.0)
    ex.execute(Order(symbol="BTC/USDT", side=Side.BUY, quantity=2.0, price=100.0))
    assert math.isclose(ex.balance("USDT"), 800.0)
    assert math.isclose(ex.balance("BTC"), 2.0)


def test_buy_charges_fee() -> None:
    ex = SimulatedExchange(balances={"USDT": 1_000.0}, fee_rate=0.01)
    fill = ex.execute(Order(symbol="BTC/USDT", side=Side.BUY, quantity=1.0, price=100.0))
    assert math.isclose(fill.fee, 1.0)
    assert math.isclose(ex.balance("USDT"), 1_000.0 - 100.0 - 1.0)


def test_sell_updates_balances() -> None:
    ex = SimulatedExchange(balances={"BTC": 3.0}, fee_rate=0.0)
    ex.execute(Order(symbol="BTC/USDT", side=Side.SELL, quantity=2.0, price=100.0))
    assert math.isclose(ex.balance("BTC"), 1.0)
    assert math.isclose(ex.balance("USDT"), 200.0)


def test_equity_marks_to_price() -> None:
    ex = SimulatedExchange(balances={"USDT": 500.0, "BTC": 2.0}, fee_rate=0.0)
    ex.set_price("BTC/USDT", 150.0)
    assert math.isclose(ex.equity("USDT"), 500.0 + 2.0 * 150.0)


def test_negative_fee_rate_raises() -> None:
    with pytest.raises(ValueError):
        SimulatedExchange(fee_rate=-0.01)

"""Tests for geometric (log-spaced) grid spacing."""

from __future__ import annotations

import math

from grid_trading_bot.exchange import SimulatedExchange
from grid_trading_bot.grid import GridSpacing, GridStrategy
from grid_trading_bot.models import Side


def test_geometric_lines_have_constant_ratio() -> None:
    strat = GridStrategy(
        lower=100.0, upper=400.0, levels=3, quantity=1.0, spacing=GridSpacing.GEOMETRIC
    )
    lines = strat.grid_lines()
    assert math.isclose(lines[0], 100.0)
    assert math.isclose(lines[1], 200.0)  # 100 * 2
    assert math.isclose(lines[2], 400.0)  # 100 * 2^2
    # Equal ratio between successive lines.
    assert math.isclose(lines[1] / lines[0], lines[2] / lines[1])


def test_geometric_endpoints_match_bounds() -> None:
    strat = GridStrategy(
        lower=50.0, upper=150.0, levels=7, quantity=1.0, spacing=GridSpacing.GEOMETRIC
    )
    lines = strat.grid_lines()
    assert math.isclose(lines[0], 50.0)
    assert math.isclose(lines[-1], 150.0)
    assert len(lines) == 7


def test_geometric_index_round_trips() -> None:
    strat = GridStrategy(
        lower=100.0, upper=400.0, levels=3, quantity=1.0, spacing=GridSpacing.GEOMETRIC
    )
    # The nearest line to each line price is that line's own index.
    for i, line in enumerate(strat.grid_lines()):
        assert strat._index_for(line) == i


def test_geometric_buys_on_dip() -> None:
    ex = SimulatedExchange(balances={"USDT": 10_000.0}, fee_rate=0.0)
    strat = GridStrategy(
        lower=80.0, upper=125.0, levels=11, quantity=1.0, spacing=GridSpacing.GEOMETRIC
    )
    strat.on_price("BTC/USDT", 100.0, ex)
    orders = strat.on_price("BTC/USDT", 85.0, ex)
    assert len(orders) == 1
    assert orders[0].side is Side.BUY


def test_geometric_differs_from_arithmetic() -> None:
    arith = GridStrategy(lower=100.0, upper=400.0, levels=3, quantity=1.0)
    geo = GridStrategy(
        lower=100.0, upper=400.0, levels=3, quantity=1.0, spacing=GridSpacing.GEOMETRIC
    )
    assert arith.grid_lines()[1] == 250.0
    assert geo.grid_lines()[1] == 200.0

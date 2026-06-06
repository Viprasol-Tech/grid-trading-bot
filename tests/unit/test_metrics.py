"""Tests for the performance-metric functions."""

from __future__ import annotations

import math

import pytest

from grid_trading_bot.metrics import cagr, max_drawdown, returns, sharpe_ratio


def test_returns_basic() -> None:
    assert returns([100.0, 110.0, 99.0]) == pytest.approx([0.1, -0.1])


def test_returns_handles_zero_base() -> None:
    assert returns([0.0, 50.0]) == [0.0]


def test_max_drawdown_simple() -> None:
    # Peak 100, trough 75 -> 25% drawdown, then recovery does not reduce it.
    assert math.isclose(max_drawdown([100.0, 75.0, 90.0]), 0.25)


def test_max_drawdown_monotonic_up_is_zero() -> None:
    assert max_drawdown([10.0, 20.0, 30.0]) == 0.0


def test_max_drawdown_empty_or_single() -> None:
    assert max_drawdown([]) == 0.0
    assert max_drawdown([100.0]) == 0.0


def test_sharpe_positive_for_steady_growth() -> None:
    curve = [100.0 * (1.01**i) for i in range(50)]
    assert sharpe_ratio(curve) > 0.0


def test_sharpe_zero_for_flat_curve() -> None:
    assert sharpe_ratio([100.0] * 10) == 0.0


def test_sharpe_too_few_points() -> None:
    assert sharpe_ratio([100.0, 101.0]) == 0.0


def test_cagr_doubling_over_one_year() -> None:
    curve = [100.0, 200.0]
    # One step at 1 period/year => 100% growth over a year.
    assert math.isclose(cagr(curve, periods_per_year=1), 1.0)


def test_cagr_handles_bad_input() -> None:
    assert cagr([100.0]) == 0.0
    assert cagr([0.0, 100.0]) == 0.0

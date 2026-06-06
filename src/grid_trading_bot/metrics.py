"""Performance metrics for an equity curve.

Pure functions over a sequence of equity values: per-tick returns, maximum
drawdown, and an (annualised) Sharpe ratio. These power the backtest report.

Part of Grid Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import pairwise

import numpy as np


def returns(equity_curve: Sequence[float]) -> list[float]:
    """Return simple per-step returns of ``equity_curve``.

    Args:
        equity_curve: Equity valued at each tick (length ``n``).

    Returns:
        A list of ``n - 1`` returns where ``r[i] = e[i+1] / e[i] - 1``. Steps
        starting from zero equity contribute ``0.0`` (no defined return).
    """
    out: list[float] = []
    for prev, cur in pairwise(equity_curve):
        out.append(0.0 if prev == 0 else cur / prev - 1.0)
    return out


def max_drawdown(equity_curve: Sequence[float]) -> float:
    """Return the maximum peak-to-trough drawdown as a non-negative fraction.

    A result of ``0.25`` means equity fell 25% below its running peak at the
    worst point. An empty or single-point curve has zero drawdown.

    Args:
        equity_curve: Equity valued at each tick.
    """
    if len(equity_curve) < 2:
        return 0.0
    arr = np.asarray(equity_curve, dtype=float)
    running_peak = np.maximum.accumulate(arr)
    safe_peak = np.where(running_peak == 0, 1.0, running_peak)
    drawdowns = (running_peak - arr) / safe_peak
    return float(np.max(drawdowns))


def sharpe_ratio(
    equity_curve: Sequence[float],
    risk_free: float = 0.0,
    periods_per_year: int = 252,
) -> float:
    """Return the annualised Sharpe ratio of ``equity_curve``.

    Computed from per-step returns: ``mean(excess) / std(excess)`` scaled by
    ``sqrt(periods_per_year)``. Returns ``0.0`` when there are fewer than two
    returns or when return volatility is zero (no risk-adjusted signal).

    Args:
        equity_curve: Equity valued at each tick.
        risk_free: Per-step risk-free return subtracted from each step.
        periods_per_year: Steps per year used to annualise (e.g. ``252`` daily).
    """
    rets = np.asarray(returns(equity_curve), dtype=float)
    if rets.size < 2:
        return 0.0
    excess = rets - risk_free
    std = float(np.std(excess, ddof=1))
    if std == 0.0:
        return 0.0
    return float(np.mean(excess) / std * np.sqrt(periods_per_year))


def cagr(equity_curve: Sequence[float], periods_per_year: int = 252) -> float:
    """Return the compound annual growth rate implied by ``equity_curve``.

    Args:
        equity_curve: Equity valued at each tick (must start ``> 0``).
        periods_per_year: Steps per year used to annualise.

    Returns:
        The annualised growth rate as a fraction, or ``0.0`` if it cannot be
        computed (too few points or non-positive start/end equity).
    """
    if len(equity_curve) < 2:
        return 0.0
    start, end = equity_curve[0], equity_curve[-1]
    if start <= 0 or end <= 0:
        return 0.0
    steps = len(equity_curve) - 1
    years = steps / periods_per_year
    if years <= 0:
        return 0.0
    return float((end / start) ** (1.0 / years) - 1.0)

"""Backtest runner for the grid strategy.

Replays a price series through a :class:`~grid_trading_bot.grid.GridStrategy`
against a :class:`~grid_trading_bot.exchange.SimulatedExchange`, recording every
fill and the equity curve, then reports the final mark-to-market equity.

Part of Grid Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from grid_trading_bot.exchange import SimulatedExchange
from grid_trading_bot.grid import GridStrategy
from grid_trading_bot.models import Fill


class BacktestResult(BaseModel):
    """Summary of a completed backtest.

    Args:
        symbol: Market the backtest ran on.
        starting_equity: Mark-to-market equity before the first tick.
        final_equity: Mark-to-market equity after the last tick.
        fills: Every fill produced, in chronological order.
        equity_curve: Equity valued at each tick, one entry per price.
    """

    model_config = ConfigDict(frozen=True)

    symbol: str
    starting_equity: float
    final_equity: float
    fills: list[Fill]
    equity_curve: list[float]

    @property
    def num_fills(self) -> int:
        """Number of orders that were filled during the backtest."""
        return len(self.fills)

    @property
    def pnl(self) -> float:
        """Absolute profit/loss in the quote asset (final minus starting)."""
        return self.final_equity - self.starting_equity

    @property
    def return_pct(self) -> float:
        """Percentage return over the backtest (``0.0`` if no starting equity)."""
        if self.starting_equity == 0:
            return 0.0
        return 100.0 * self.pnl / self.starting_equity


def run_backtest(
    symbol: str,
    prices: Sequence[float],
    strategy: GridStrategy,
    exchange: SimulatedExchange,
    quote: str = "USDT",
) -> BacktestResult:
    """Replay ``prices`` through ``strategy`` on ``exchange`` and summarise it.

    For each price the exchange is marked to that price, the strategy is asked
    for orders, each order is executed, and the resulting equity is recorded.

    Args:
        symbol: Market symbol in ``BASE/QUOTE`` form (e.g. ``BTC/USDT``).
        prices: The price series to replay (must be non-empty).
        strategy: The grid strategy to drive.
        exchange: The simulated exchange holding balances and fees.
        quote: Quote asset used to value equity.

    Returns:
        A :class:`BacktestResult` with final equity, fills, and the equity curve.

    Raises:
        ValueError: If ``prices`` is empty.
    """
    if not prices:
        raise ValueError("prices must contain at least one value")

    exchange.set_price(symbol, prices[0])
    starting_equity = exchange.equity(quote)

    fills: list[Fill] = []
    equity_curve: list[float] = []
    for price in prices:
        exchange.set_price(symbol, price)
        for order in strategy.on_price(symbol, price, exchange):
            fills.append(exchange.execute(order))
        equity_curve.append(exchange.equity(quote))

    return BacktestResult(
        symbol=symbol,
        starting_equity=starting_equity,
        final_equity=equity_curve[-1],
        fills=fills,
        equity_curve=equity_curve,
    )

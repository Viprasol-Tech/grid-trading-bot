"""Grid trading strategy.

Lays a ladder of price levels between ``lower`` and ``upper``. Levels can be
spaced **arithmetically** (equal price distance) or **geometrically** (equal
ratio, i.e. log-spaced — natural for assets that move in percentage terms). As
price falls through a grid line the strategy buys; as it rises through a line it
sells (when enough base asset is held). A classic, fully mechanical range-trading
approach that harvests volatility in a sideways market.

Optional risk controls:

* **Take-profit / stop bounds** — if price trades at or above ``take_profit`` or
  at or below ``stop_loss`` the strategy liquidates its base inventory once and
  goes dormant, so a breakout does not bleed the grid.
* **Trailing grid** — when enabled, a breakout *above* the grid slides the whole
  ladder upward to re-center on the new price, letting the grid follow a trend
  instead of selling out at the top.

Part of Grid Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math
from enum import Enum

from grid_trading_bot.exchange import SimulatedExchange
from grid_trading_bot.models import Order, Side


class GridSpacing(str, Enum):
    """How grid levels are distributed between ``lower`` and ``upper``."""

    ARITHMETIC = "arithmetic"
    GEOMETRIC = "geometric"


class GridStrategy:
    """Buy as price falls through grid lines, sell as it rises through them.

    The grid has ``levels`` lines from ``lower`` to ``upper``. With
    :attr:`GridSpacing.ARITHMETIC` spacing the lines are equally far apart in
    price; with :attr:`GridSpacing.GEOMETRIC` they are equally far apart in
    ratio (log-spaced), so each step is the same *percentage* move.

    Args:
        lower: Bottom of the price grid (must be ``> 0``).
        upper: Top of the price grid (must be ``> lower``).
        levels: Number of grid lines (must be ``>= 2``).
        quantity: Base-asset quantity traded each time a line is crossed.
        spacing: Arithmetic or geometric level distribution.
        take_profit: Liquidate inventory and stop if price reaches this level
            (must be ``> 0`` when set).
        stop_loss: Liquidate inventory and stop if price falls to this level
            (must be ``> 0`` when set).
        trailing: If ``True`` the grid slides up to re-center when price breaks
            above ``upper``, following an uptrend instead of selling out.

    Raises:
        ValueError: If ``lower <= 0``, ``upper <= lower``, ``levels < 2``,
            ``quantity <= 0``, a bound is non-positive, or ``trailing`` is
            combined with ``take_profit`` (they contradict each other).
    """

    name = "grid"

    def __init__(
        self,
        lower: float,
        upper: float,
        levels: int,
        quantity: float,
        spacing: GridSpacing = GridSpacing.ARITHMETIC,
        take_profit: float | None = None,
        stop_loss: float | None = None,
        trailing: bool = False,
    ) -> None:
        if lower <= 0:
            raise ValueError("lower must be greater than 0")
        if upper <= lower:
            raise ValueError("upper must be greater than lower")
        if levels < 2:
            raise ValueError("levels must be >= 2")
        if quantity <= 0:
            raise ValueError("quantity must be greater than 0")
        if take_profit is not None and take_profit <= 0:
            raise ValueError("take_profit must be greater than 0")
        if stop_loss is not None and stop_loss <= 0:
            raise ValueError("stop_loss must be greater than 0")
        if trailing and take_profit is not None:
            raise ValueError("trailing and take_profit cannot be combined")

        self.lower = lower
        self.upper = upper
        self.levels = levels
        self.quantity = quantity
        self.spacing = spacing
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.trailing = trailing

        self._recompute_lines()
        self._last_index: int | None = None
        self._stopped = False

    def _recompute_lines(self) -> None:
        """(Re)compute grid line prices and the spacing step from the bounds."""
        if self.spacing is GridSpacing.GEOMETRIC:
            ratio = (self.upper / self.lower) ** (1.0 / (self.levels - 1))
            self._lines = [self.lower * ratio**i for i in range(self.levels)]
            self.step = ratio
        else:
            step = (self.upper - self.lower) / (self.levels - 1)
            self._lines = [self.lower + i * step for i in range(self.levels)]
            self.step = step

    def grid_lines(self) -> list[float]:
        """Return the absolute prices of every grid line, low to high."""
        return list(self._lines)

    @property
    def stopped(self) -> bool:
        """True once a take-profit/stop bound has liquidated the grid."""
        return self._stopped

    def _index_for(self, price: float) -> int:
        """Return the index (0..levels-1) of the nearest grid line to ``price``."""
        clamped = min(max(price, self.lower), self.upper)
        if self.spacing is GridSpacing.GEOMETRIC:
            offset: float = math.log(clamped / self.lower) / math.log(self.step)
        else:
            offset = (clamped - self.lower) / self.step
        index: int = round(offset)
        return index

    def _liquidate(self, symbol: str, price: float, exchange: SimulatedExchange) -> list[Order]:
        """Sell all held base inventory at ``price`` and mark the grid stopped."""
        self._stopped = True
        base = symbol.split("/")[0]
        held = exchange.balance(base)
        if held <= 0:
            return []
        return [Order(symbol=symbol, side=Side.SELL, quantity=held, price=price)]

    def on_price(self, symbol: str, price: float, exchange: SimulatedExchange) -> list[Order]:
        """React to a new ``price`` tick and return any orders to execute.

        On the first tick the strategy only records its grid position. On later
        ticks it emits a BUY when price has dropped to a lower grid index and a
        SELL when it has risen to a higher index (and the base balance suffices).

        Take-profit / stop bounds (if set) are checked first and trigger a
        one-time liquidation. When ``trailing`` is enabled and price breaks above
        ``upper`` the grid re-centers upward instead of selling out.

        Args:
            symbol: Market symbol in ``BASE/QUOTE`` form.
            price: The latest traded price.
            exchange: Exchange used to check available base balance for sells.

        Returns:
            A list of zero or more :class:`Order` for this tick.
        """
        if self._stopped:
            return []

        if self.take_profit is not None and price >= self.take_profit:
            return self._liquidate(symbol, price, exchange)
        if self.stop_loss is not None and price <= self.stop_loss:
            return self._liquidate(symbol, price, exchange)

        if self.trailing and price > self.upper:
            self._slide_up(price)

        index = self._index_for(price)
        if self._last_index is None:
            self._last_index = index
            return []

        orders: list[Order] = []
        if index < self._last_index:
            orders.append(Order(symbol=symbol, side=Side.BUY, quantity=self.quantity, price=price))
        elif index > self._last_index:
            base = symbol.split("/")[0]
            if exchange.balance(base) >= self.quantity:
                orders.append(
                    Order(symbol=symbol, side=Side.SELL, quantity=self.quantity, price=price)
                )
        self._last_index = index
        return orders

    def _slide_up(self, price: float) -> None:
        """Shift the whole grid up so its top sits at ``price`` (trailing mode)."""
        width = self.upper - self.lower if self.spacing is GridSpacing.ARITHMETIC else None
        if width is not None:
            self.lower = price - width
            self.upper = price
        else:
            factor = price / self.upper
            self.lower *= factor
            self.upper = price
        self._recompute_lines()
        self._last_index = self._index_for(price)

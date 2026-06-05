"""Grid trading strategy.

Lays a ladder of evenly spaced price levels between ``lower`` and ``upper``. As
price falls through a grid line the strategy buys; as it rises through a line it
sells (when enough base asset is held). A classic, fully mechanical range-trading
approach that harvests volatility in a sideways market.

Part of Grid Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from grid_trading_bot.exchange import SimulatedExchange
from grid_trading_bot.models import Order, Side


class GridStrategy:
    """Buy as price falls through grid lines, sell as it rises through them.

    The grid has ``levels`` evenly spaced lines from ``lower`` to ``upper``, so
    the spacing between adjacent lines is ``(upper - lower) / (levels - 1)``.

    Args:
        lower: Bottom of the price grid (must be ``> 0``).
        upper: Top of the price grid (must be ``> lower``).
        levels: Number of grid lines (must be ``>= 2``).
        quantity: Base-asset quantity traded each time a line is crossed.

    Raises:
        ValueError: If ``lower <= 0``, ``upper <= lower``, ``levels < 2``, or
            ``quantity <= 0``.
    """

    name = "grid"

    def __init__(self, lower: float, upper: float, levels: int, quantity: float) -> None:
        if lower <= 0:
            raise ValueError("lower must be greater than 0")
        if upper <= lower:
            raise ValueError("upper must be greater than lower")
        if levels < 2:
            raise ValueError("levels must be >= 2")
        if quantity <= 0:
            raise ValueError("quantity must be greater than 0")
        self.lower = lower
        self.upper = upper
        self.levels = levels
        self.quantity = quantity
        self.step = (upper - lower) / (levels - 1)
        self._last_index: int | None = None

    def grid_lines(self) -> list[float]:
        """Return the absolute prices of every grid line, low to high."""
        return [self.lower + i * self.step for i in range(self.levels)]

    def _index_for(self, price: float) -> int:
        """Return the index (0..levels-1) of the nearest grid line to ``price``."""
        clamped = min(max(price, self.lower), self.upper)
        return round((clamped - self.lower) / self.step)

    def on_price(self, symbol: str, price: float, exchange: SimulatedExchange) -> list[Order]:
        """React to a new ``price`` tick and return any orders to execute.

        On the first tick the strategy only records its grid position. On later
        ticks it emits a BUY when price has dropped to a lower grid index and a
        SELL when it has risen to a higher index (and the base balance suffices).

        Args:
            symbol: Market symbol in ``BASE/QUOTE`` form.
            price: The latest traded price.
            exchange: Exchange used to check available base balance for sells.

        Returns:
            A list of zero or one :class:`Order` for this tick.
        """
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

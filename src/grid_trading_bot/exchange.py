"""A simulated exchange for paper trading and backtests.

Holds base/quote balances and fills orders instantly at a given price, charging a
proportional fee. Symbols are ``BASE/QUOTE`` (e.g. ``BTC/USDT``).

Part of Grid Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from grid_trading_bot.models import Fill, Order, Side


class SimulatedExchange:
    """In-memory exchange with configurable fees and balances.

    Args:
        balances: Starting balances keyed by asset (e.g. ``{"USDT": 10_000}``).
        fee_rate: Proportional fee on each fill's notional (e.g. ``0.001`` = 10 bps).

    Raises:
        ValueError: If ``fee_rate`` is negative.
    """

    def __init__(self, balances: dict[str, float] | None = None, fee_rate: float = 0.001) -> None:
        if fee_rate < 0:
            raise ValueError("fee_rate must be non-negative")
        self._balances: dict[str, float] = dict(balances or {})
        self._prices: dict[str, float] = {}
        self.fee_rate = fee_rate

    def set_price(self, symbol: str, price: float) -> None:
        """Update the current price used for fills and equity valuation."""
        self._prices[symbol] = price

    def price(self, symbol: str) -> float:
        """Return the last known price for ``symbol`` (``0.0`` if unseen)."""
        return self._prices.get(symbol, 0.0)

    def balance(self, asset: str) -> float:
        """Return the held quantity of ``asset`` (``0.0`` if none)."""
        return self._balances.get(asset, 0.0)

    def execute(self, order: Order) -> Fill:
        """Fill ``order`` at its price, updating balances and charging the fee.

        Buys debit the quote asset (notional + fee) and credit the base asset.
        Sells credit the quote asset (notional - fee) and debit the base asset.

        Args:
            order: The order to execute.

        Returns:
            A :class:`Fill` recording the order and the fee paid.
        """
        base, quote = order.symbol.split("/")
        notional = order.notional
        fee = notional * self.fee_rate
        if order.side is Side.BUY:
            self._balances[quote] = self.balance(quote) - notional - fee
            self._balances[base] = self.balance(base) + order.quantity
        else:
            self._balances[base] = self.balance(base) - order.quantity
            self._balances[quote] = self.balance(quote) + notional - fee
        return Fill(order=order, fee=fee)

    def equity(self, quote: str = "USDT") -> float:
        """Total equity valued in ``quote`` at the latest known prices.

        Sums the quote balance plus every base balance marked to its last price.
        """
        total = self.balance(quote)
        for symbol, price in self._prices.items():
            base = symbol.split("/")[0]
            total += self.balance(base) * price
        return total

"""Command-line interface for Grid Trading Bot.

``grid-trading-bot demo`` runs the grid strategy on a synthetic sine price series
against the simulated exchange and prints the backtest summary — no API keys, no
risk.

Part of Grid Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math

import typer
from rich.console import Console

from grid_trading_bot import __version__
from grid_trading_bot.backtest import run_backtest
from grid_trading_bot.exchange import SimulatedExchange
from grid_trading_bot.grid import GridStrategy

app = typer.Typer(add_completion=False, help="Grid Trading Bot — by Viprasol Tech.")
console = Console()


def synthetic_prices(n: int = 200, base: float = 100.0, amplitude: float = 15.0) -> list[float]:
    """Return a synthetic sine-wave price series for demos and tests.

    Args:
        n: Number of price points to generate.
        base: Mid-price the wave oscillates around.
        amplitude: Peak deviation from ``base``.

    Returns:
        A list of ``n`` prices following ``base + amplitude * sin(i / 10)``.
    """
    return [base + amplitude * math.sin(i / 10.0) for i in range(n)]


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"grid-trading-bot [bold cyan]{__version__}[/] - by Viprasol Tech")


@app.command()
def demo(
    lower: float = typer.Option(85.0, help="Bottom of the price grid."),
    upper: float = typer.Option(115.0, help="Top of the price grid."),
    levels: int = typer.Option(13, help="Number of grid lines (>= 2)."),
    quantity: float = typer.Option(1.0, help="Base quantity traded per level."),
    cash: float = typer.Option(10_000.0, help="Starting quote balance (USDT)."),
) -> None:
    """Run a grid backtest on a synthetic sine series against the sim exchange."""
    symbol = "BTC/USDT"
    prices = synthetic_prices()
    exchange = SimulatedExchange(balances={"USDT": cash})
    try:
        strategy = GridStrategy(lower=lower, upper=upper, levels=levels, quantity=quantity)
    except ValueError as exc:
        console.print(f"[red]Invalid grid: {exc}[/]")
        raise typer.Exit(code=1) from exc

    result = run_backtest(symbol, prices, strategy, exchange)
    console.print(f"Strategy:     [bold]{strategy.name}[/] ({levels} levels {lower}-{upper})")
    console.print(f"Ticks:        {len(prices)}")
    console.print(f"Fills:        {result.num_fills}")
    console.print(f"Start equity: ${result.starting_equity:,.2f}")
    console.print(
        f"Final equity: [bold green]${result.final_equity:,.2f}[/] ({result.return_pct:+.2f}%)"
    )


if __name__ == "__main__":
    app()

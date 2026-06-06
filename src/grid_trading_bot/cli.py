"""Command-line interface for Grid Trading Bot.

Subcommands:

* ``version``      — print the installed version.
* ``demo``         — run the grid on a synthetic sine series (no keys, no risk).
* ``backtest``     — run a backtest from a JSON config and print a full report.
* ``init-config``  — write a starter config file you can edit and re-run.

Part of Grid Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from grid_trading_bot import __version__
from grid_trading_bot.backtest import BacktestResult, run_backtest
from grid_trading_bot.config import BotConfig
from grid_trading_bot.exchange import SimulatedExchange
from grid_trading_bot.grid import GridSpacing, GridStrategy

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


def render_report(result: BacktestResult, title: str) -> None:
    """Print a rich table summarising a :class:`BacktestResult`."""
    table = Table(title=title, title_style="bold cyan", show_header=False)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Symbol", result.symbol)
    table.add_row("Ticks", str(len(result.equity_curve)))
    table.add_row("Fills", f"{result.num_fills} ({result.num_buys} buy / {result.num_sells} sell)")
    table.add_row("Fees paid", f"${result.total_fees:,.2f}")
    table.add_row("Start equity", f"${result.starting_equity:,.2f}")
    final = f"${result.final_equity:,.2f} ({result.return_pct:+.2f}%)"
    table.add_row("Final equity", f"[bold green]{final}[/]")
    table.add_row("Max drawdown", f"{result.max_drawdown_pct:.2f}%")
    table.add_row("Sharpe", f"{result.sharpe():.2f}")
    console.print(table)


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
    spacing: GridSpacing = typer.Option(GridSpacing.ARITHMETIC, help="Grid spacing mode."),
) -> None:
    """Run a grid backtest on a synthetic sine series against the sim exchange."""
    symbol = "BTC/USDT"
    prices = synthetic_prices()
    exchange = SimulatedExchange(balances={"USDT": cash})
    try:
        strategy = GridStrategy(
            lower=lower, upper=upper, levels=levels, quantity=quantity, spacing=spacing
        )
    except ValueError as exc:
        console.print(f"[red]Invalid grid: {exc}[/]")
        raise typer.Exit(code=1) from exc

    result = run_backtest(symbol, prices, strategy, exchange)
    render_report(result, f"Demo backtest — {spacing.value} grid ({levels} levels)")


@app.command()
def backtest(
    config: Path = typer.Argument(..., help="Path to a JSON config file."),
    prices_csv: Path | None = typer.Option(
        None, "--prices", help="Optional CSV/newline file of prices (one per line)."
    ),
) -> None:
    """Run a backtest from a JSON config, optionally on real prices, and report."""
    try:
        cfg = BotConfig.from_file(config)
    except (OSError, ValueError) as exc:
        console.print(f"[red]Could not load config: {exc}[/]")
        raise typer.Exit(code=1) from exc

    if prices_csv is not None:
        prices = load_prices(prices_csv)
        if not prices:
            console.print("[red]No prices found in file.[/]")
            raise typer.Exit(code=1)
    else:
        prices = synthetic_prices(base=(cfg.lower + cfg.upper) / 2.0)

    result = run_backtest(cfg.symbol, prices, cfg.build_strategy(), cfg.build_exchange(), cfg.quote)
    render_report(result, f"Backtest — {cfg.symbol} ({cfg.spacing.value})")


@app.command("init-config")
def init_config(
    path: Path = typer.Argument(Path("grid.json"), help="Where to write the config."),
    force: bool = typer.Option(False, "--force", help="Overwrite if the file exists."),
) -> None:
    """Write a starter JSON config you can edit and feed to ``backtest``."""
    if path.exists() and not force:
        console.print(f"[red]{path} exists. Pass --force to overwrite.[/]")
        raise typer.Exit(code=1)
    BotConfig().to_file(path)
    console.print(f"[green]Wrote starter config to {path}[/]")


def load_prices(path: Path) -> list[float]:
    """Parse a newline/CSV file of prices into a list of floats.

    Blank lines are skipped; each remaining line's first comma-field is parsed.

    Args:
        path: File containing one price per line (optionally CSV).
    """
    prices: list[float] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        token = line.strip().split(",")[0].strip()
        if token:
            prices.append(float(token))
    return prices


if __name__ == "__main__":
    app()

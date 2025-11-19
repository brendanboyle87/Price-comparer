from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from typing import List

import typer
from rich.console import Console
from rich.table import Table

from .config import load_raw_config, load_resolved_config, save_resolved_config
from .discovery import discover_products
from .models import AppConfig, ComparisonRow, PriceResult
from .stores import GiantClient, TargetClient

app = typer.Typer(help="Compare grocery prices across stores.")
console = Console()


@app.command()
def discover(
    raw_config: Path = typer.Option(Path("data/products_raw.yaml"), help="Raw products file"),
    output: Path = typer.Option(Path("data/products_resolved.yaml"), help="Resolved config output"),
    interactive: bool = typer.Option(False, "-i", "--interactive", help="Interactive selection"),
):
    """Discover store identifiers for each product."""

    raw = load_raw_config(raw_config)
    app_config = asyncio.run(discover_products(raw, interactive=interactive))
    save_resolved_config(app_config, output)
    console.print(f"Resolved {len(app_config.products)} products -> {output}")


@app.command()
def compare(
    config: Path = typer.Option(Path("data/products_resolved.yaml"), help="Resolved config file"),
    output: str = typer.Option("table", help="Output format: table/json/csv"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose logging"),
):
    """Fetch live prices and compare stores."""

    app_config = load_resolved_config(config)
    results = asyncio.run(_fetch_prices(app_config))
    rows = _build_comparison_rows(app_config, results)

    if output == "json":
        console.print_json(json.dumps([row.model_dump() for row in rows], default=str))
    elif output == "csv":
        _print_csv(rows)
    else:
        _print_table(rows)

    if verbose:
        for result in results:
            console.log(result.model_dump())


@app.command("list-products")
def list_products(config: Path = typer.Option(Path("data/products_resolved.yaml"), help="Resolved config")):
    """List resolved products and identifiers."""

    app_config = load_resolved_config(config)
    table = Table(title="Products")
    table.add_column("Name")
    table.add_column("Target TCIN")
    table.add_column("Giant Slug")
    for product in app_config.products:
        table.add_row(
            product.name,
            product.target.tcin if product.target else "",
            product.giant.slug if product.giant else "",
        )
    console.print(table)


async def _fetch_prices(app_config: AppConfig) -> List[PriceResult]:
    target_client = TargetClient(
        store_id=app_config.defaults.get("target_store_id"),
        zip_code=app_config.defaults.get("target_zip"),
    )
    giant_client = GiantClient()

    tasks = []
    for product in app_config.products:
        tasks.append(target_client.get_price(product))
        tasks.append(giant_client.get_price(product))
    return await asyncio.gather(*tasks)


def _build_comparison_rows(app_config: AppConfig, results: List[PriceResult]) -> List[ComparisonRow]:
    rows: List[ComparisonRow] = []
    result_map: dict[str, dict[str, PriceResult]] = {}
    for result in results:
        result_map.setdefault(result.product_name, {})[result.store] = result

    for product in app_config.products:
        target_price = result_map.get(product.name, {}).get("target")
        giant_price = result_map.get(product.name, {}).get("giant")
        row = ComparisonRow.from_prices(
            product.name,
            target_price.price if target_price else None,
            giant_price.price if giant_price else None,
        )
        rows.append(row)
    return rows


def _print_table(rows: List[ComparisonRow]) -> None:
    table = Table(title="Price Comparison")
    table.add_column("Product")
    table.add_column("Target")
    table.add_column("Giant")
    table.add_column("Cheaper")
    table.add_column("Savings")

    for row in rows:
        table.add_row(
            row.product_name,
            _format_price(row.target_price),
            _format_price(row.giant_price),
            row.cheaper_store or "-",
            _format_price(row.savings),
        )
    console.print(table)


def _print_csv(rows: List[ComparisonRow]) -> None:
    writer = csv.DictWriter(
        console.file,
        fieldnames=["product_name", "target_price", "giant_price", "cheaper_store", "savings"],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row.model_dump())


def _format_price(value: float | None) -> str:
    if value is None:
        return "-"
    return f"${value:0.2f}"


if __name__ == "__main__":
    app()

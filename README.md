# Price-comparer

CLI tool to discover grocery product identifiers on Target and Giant, then compare live prices.

## Setup

Install dependencies with [uv](https://github.com/astral-sh/uv) or your preferred tool. The project targets Python 3.12.

```bash
uv sync
```

## Usage

Discover store identifiers for human-readable products and write them to `data/products_resolved.yaml`:

```bash
uv run price-compare discover --raw-config data/products_raw.yaml --output data/products_resolved.yaml
```

Fetch live prices and render a comparison table:

```bash
uv run price-compare compare --config data/products_resolved.yaml
```

List resolved products:

```bash
uv run price-compare list-products --config data/products_resolved.yaml
```

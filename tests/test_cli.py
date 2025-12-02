import json
from pathlib import Path

from typer.testing import CliRunner

from price_comparator import cli
from price_comparator.models import PriceResult

runner = CliRunner()


def test_list_products(tmp_path: Path):
    config_path = tmp_path / "resolved.yaml"
    config_path.write_text((Path(__file__).parent.parent / "src/price_comparator/data/products_resolved.yaml").read_text())
    result = runner.invoke(cli.app, ["list-products", "--config", str(config_path)])
    assert result.exit_code == 0
    assert "Whole Milk" in result.stdout


def test_compare_outputs_json(monkeypatch, tmp_path: Path):
    config_path = tmp_path / "resolved.yaml"
    config_path.write_text((Path(__file__).parent.parent / "src/price_comparator/data/products_resolved.yaml").read_text())

    async def fake_fetch_prices(app_config):  # noqa: ANN001
        return [
            PriceResult(store="target", product_name="Whole Milk 1 gal", price=3.5, currency="USD"),
            PriceResult(store="giant", product_name="Whole Milk 1 gal", price=3.0, currency="USD"),
        ]

    monkeypatch.setattr(cli, "_fetch_prices", fake_fetch_prices)

    result = runner.invoke(cli.app, ["compare", "--config", str(config_path), "--output", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data[0]["cheaper_store"] == "giant"

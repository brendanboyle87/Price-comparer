import asyncio

from price_comparator.discovery import discover_products, similarity_score
from price_comparator.models import RawConfig, RawProduct


def test_similarity_score_closer():
    assert similarity_score("Whole Milk", "Whole Milk 1 gal") > similarity_score("Whole Milk", "Orange Juice")


def test_discover_products_uses_search(monkeypatch):
    target_html = """
    <html><body>
    <a data-test='product-title' data-tcin='999' href='/p/test-milk/-/A-999'>Test Milk 1 gal</a>
    </body></html>
    """
    giant_html = """
    <html><body>
    <a href='/grocery/test-milk'>Test Milk 1 gal</a>
    </body></html>
    """

    async def fake_fetch(url, params=None):  # noqa: ANN001
        if "target" in url:
            return target_html
        return giant_html

    monkeypatch.setattr("price_comparator.discovery._safe_fetch", fake_fetch)

    raw = RawConfig(defaults={}, products=[RawProduct(name="Test Milk 1 gal")])
    app_config = asyncio.run(discover_products(raw))

    product = app_config.products[0]
    assert product.target.tcin == "999"
    assert product.giant.slug == "test-milk"

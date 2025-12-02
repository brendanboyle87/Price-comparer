from __future__ import annotations

from typing import Any, Optional

from ..models import PriceResult, ProductConfig
from ..utils.http import get_html
from ..utils.parsing import parse_giant_product_html
from .base import StoreClient


class GiantClient(StoreClient):
    store_name = "giant"

    def __init__(self, base_url: str = "https://giantfood.com", client: Any = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client

    async def get_price(self, product: ProductConfig) -> PriceResult:
        url = self._build_url(product)
        try:
            html = await get_html(url)
            price = parse_giant_product_html(html)
            if price is not None:
                return PriceResult(
                    store=self.store_name,
                    product_name=product.name,
                    price=price,
                    currency="USD",
                    product_url=url,
                )
            error_msg = "Unable to parse price from Giant page"
        except Exception as exc:  # pragma: no cover - real network failures
            error_msg = str(exc)
        return PriceResult(
            store=self.store_name,
            product_name=product.name,
            price=None,
            currency="USD",
            product_url=url,
            error=error_msg,
        )

    def _build_url(self, product: ProductConfig) -> str:
        if product.giant and product.giant.url:
            return product.giant.url
        if product.giant and product.giant.slug:
            return f"{self.base_url}/grocery/{product.giant.slug}"
        if product.giant and product.giant.product_id:
            return f"{self.base_url}/product/{product.giant.product_id}"
        # fallback to search if nothing else
        return f"{self.base_url}/s/?q={product.name.replace(' ', '+')}"

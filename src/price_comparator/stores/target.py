from __future__ import annotations

from typing import Any, Optional

from ..models import PriceResult, ProductConfig
from ..utils.http import get_html, get_json
from ..utils.parsing import parse_target_product_html, parse_target_product_json
from .base import StoreClient


class TargetClient(StoreClient):
    store_name = "target"

    def __init__(
        self,
        store_id: Optional[str] = None,
        zip_code: Optional[str] = None,
        client: Any = None,
    ) -> None:
        self.store_id = store_id
        self.zip_code = zip_code
        self.client = client

    async def get_price(self, product: ProductConfig) -> PriceResult:
        tcin = product.target.tcin if product.target else None
        url = product.target.url if product.target else None
        if not tcin:
            return PriceResult(
                store=self.store_name,
                product_name=product.name,
                price=None,
                currency="USD",
                product_url=url,
                error="Missing TCIN",
            )

        api_url = "https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1"
        params = {
            "tcin": tcin,
            "store_id": self.store_id,
            "pricing_store_id": self.store_id,
            "scheduled_delivery_store_id": self.store_id,
            "zip": self.zip_code,
            "has_store_id": True,
            "key": "eb2551adbd4c9a1b0a1fd66af84c5df9",
        }
        try:
            data = await get_json(api_url, params=params)
            price = parse_target_product_json(data)
            if price is not None:
                return PriceResult(
                    store=self.store_name,
                    product_name=product.name,
                    price=price,
                    currency="USD",
                    product_url=url,
                )
        except Exception as exc:  # pragma: no cover - real network failures
            error_msg = str(exc)
        else:
            error_msg = "Unable to parse price from Target API"

        try:
            page_url = url or f"https://www.target.com/p/-/A-{tcin}"
            html = await get_html(page_url)
            price = parse_target_product_html(html)
            if price is not None:
                return PriceResult(
                    store=self.store_name,
                    product_name=product.name,
                    price=price,
                    currency="USD",
                    product_url=page_url,
                )
        except Exception as exc:  # pragma: no cover
            error_msg = str(exc)

        return PriceResult(
            store=self.store_name,
            product_name=product.name,
            price=None,
            currency="USD",
            product_url=url or f"https://www.target.com/p/-/A-{tcin}",
            error=error_msg,
        )

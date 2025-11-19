from __future__ import annotations

import abc

from ..models import PriceResult, ProductConfig


class StoreClient(abc.ABC):
    store_name: str

    @abc.abstractmethod
    async def get_price(self, product: ProductConfig) -> PriceResult:
        """Fetch live price for a product."""

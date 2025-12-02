from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StoreTargetConfig(BaseModel):
    tcin: Optional[str] = None
    url: Optional[str] = None


class StoreGiantConfig(BaseModel):
    product_id: Optional[str] = None
    slug: Optional[str] = None
    url: Optional[str] = None


class ProductConfig(BaseModel):
    name: str
    target: Optional[StoreTargetConfig] = None
    giant: Optional[StoreGiantConfig] = None


class RawProduct(BaseModel):
    name: str


class RawConfig(BaseModel):
    defaults: Dict[str, Any] = Field(default_factory=dict)
    products: List[RawProduct] = Field(default_factory=list)


class AppConfig(BaseModel):
    defaults: Dict[str, Any] = Field(default_factory=dict)
    products: List[ProductConfig] = Field(default_factory=list)


class PriceResult(BaseModel):
    store: str
    product_name: str
    price: Optional[float]
    currency: Optional[str] = None
    product_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None


class ComparisonRow(BaseModel):
    product_name: str
    target_price: Optional[float] = None
    giant_price: Optional[float] = None
    cheaper_store: Optional[str] = None
    savings: Optional[float] = None

    @classmethod
    def from_prices(
        cls, product_name: str, target_price: Optional[float], giant_price: Optional[float]
    ) -> "ComparisonRow":
        cheaper_store = None
        savings = None
        if target_price is not None and giant_price is not None:
            if target_price < giant_price:
                cheaper_store = "target"
                savings = round(giant_price - target_price, 2)
            elif giant_price < target_price:
                cheaper_store = "giant"
                savings = round(target_price - giant_price, 2)
            else:
                cheaper_store = "equal"
                savings = 0.0
        return cls(
            product_name=product_name,
            target_price=target_price,
            giant_price=giant_price,
            cheaper_store=cheaper_store,
            savings=savings,
        )

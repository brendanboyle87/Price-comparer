from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

PRICE_RE = re.compile(r"\$?\s*([0-9]+(?:\.[0-9]{1,2})?)")


def _parse_price_value(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = PRICE_RE.search(value)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
    return None


def extract_ld_json_blocks(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    blocks: List[Dict[str, Any]] = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "{}")
            if isinstance(data, list):
                blocks.extend([item for item in data if isinstance(item, dict)])
            elif isinstance(data, dict):
                blocks.append(data)
        except json.JSONDecodeError:
            continue
    return blocks


def parse_target_product_json(data: Dict[str, Any]) -> Optional[float]:
    product = data
    for key in ("data", "product", "price"):
        if isinstance(product, dict) and key in product:
            product = product[key]
        else:
            break
    price = _parse_price_value(product) if not isinstance(product, dict) else None
    if price is not None:
        return price

    if isinstance(product, dict):
        for candidate in (
            product.get("current_retail"),
            product.get("current"),
            product.get("offer_price"),
            product.get("formatted_current_price"),
        ):
            price = _parse_price_value(candidate)
            if price is not None:
                return price
    return None


def parse_target_product_html(html: str) -> Optional[float]:
    ld_blocks = extract_ld_json_blocks(html)
    for block in ld_blocks:
        offers = block.get("offers") if isinstance(block, dict) else None
        if isinstance(offers, dict):
            price = _parse_price_value(offers.get("price"))
            if price is not None:
                return price
    soup = BeautifulSoup(html, "html.parser")
    meta_price = soup.find("meta", attrs={"itemprop": "price"})
    if meta_price and meta_price.get("content"):
        price = _parse_price_value(meta_price["content"])
        if price is not None:
            return price
    price_tags = soup.select("span[data-test='product-price']", limit=1)
    if price_tags:
        price = _parse_price_value(price_tags[0].get_text())
        if price is not None:
            return price
    text = soup.get_text(separator=" ")
    return _parse_price_value(text)


def parse_giant_product_html(html: str) -> Optional[float]:
    ld_blocks = extract_ld_json_blocks(html)
    for block in ld_blocks:
        offers = block.get("offers") if isinstance(block, dict) else None
        if isinstance(offers, dict):
            price = _parse_price_value(offers.get("price"))
            if price is not None:
                return price
    soup = BeautifulSoup(html, "html.parser")
    price_span = soup.select_one("span.price") or soup.select_one("span.pdp-price__value")
    if price_span:
        price = _parse_price_value(price_span.get_text())
        if price is not None:
            return price
    text = soup.get_text(separator=" ")
    return _parse_price_value(text)

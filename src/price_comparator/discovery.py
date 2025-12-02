from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

from bs4 import BeautifulSoup

from .models import AppConfig, ProductConfig, RawConfig, StoreGiantConfig, StoreTargetConfig
from .utils.http import get_html

logger = logging.getLogger(__name__)


@dataclass
class Candidate:
    name: str
    identifier: str
    url: str
    score: float


async def discover_products(raw_config: RawConfig, interactive: bool = False) -> AppConfig:
    products: List[ProductConfig] = []
    for raw_product in raw_config.products:
        target_cfg = await _discover_target(raw_product.name)
        giant_cfg = await _discover_giant(raw_product.name)
        product_config = ProductConfig(name=raw_product.name, target=target_cfg, giant=giant_cfg)
        products.append(product_config)
    return AppConfig(defaults=raw_config.defaults, products=products)


def similarity_score(name1: str, name2: str) -> float:
    from difflib import SequenceMatcher

    normalized1 = name1.lower().strip()
    normalized2 = name2.lower().strip()
    return SequenceMatcher(None, normalized1, normalized2).ratio()


async def _discover_target(query: str) -> Optional[StoreTargetConfig]:
    search_url = "https://www.target.com/s"
    html = await _safe_fetch(search_url, params={"searchTerm": query})
    if html is None:
        return None
    candidates = _parse_target_search_results(html, base_url="https://www.target.com")
    best = _pick_best_candidate(query, candidates)
    if best:
        return StoreTargetConfig(tcin=best.identifier, url=best.url)
    logger.warning("No Target match found for %s", query)
    return None


async def _discover_giant(query: str) -> Optional[StoreGiantConfig]:
    search_url = "https://giantfood.com/search"
    html = await _safe_fetch(search_url, params={"q": query})
    if html is None:
        return None
    candidates = _parse_giant_search_results(html, base_url="https://giantfood.com")
    best = _pick_best_candidate(query, candidates)
    if best:
        slug = best.identifier if "/" not in best.identifier else best.identifier.strip("/").split("/")[-1]
        return StoreGiantConfig(slug=slug, url=best.url)
    logger.warning("No Giant match found for %s", query)
    return None


async def _safe_fetch(url: str, params: Optional[dict] = None) -> Optional[str]:
    try:
        return await get_html(url, params=params)
    except Exception as exc:  # pragma: no cover - network errors
        logger.warning("Failed to fetch %s: %s", url, exc)
        return None


def _pick_best_candidate(query: str, candidates: List[Candidate]) -> Optional[Candidate]:
    if not candidates:
        return None
    for candidate in candidates:
        candidate.score = similarity_score(query, candidate.name)
    sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
    best = sorted_candidates[0]
    if best.score < 0.3:
        return None
    return best


def _parse_target_search_results(html: str, base_url: str) -> List[Candidate]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: List[Candidate] = []
    for product in soup.select("a[data-test='product-title']"):
        name = product.get_text(strip=True)
        href = product.get("href", "")
        tcin = product.get("data-tcin") or _extract_tcin_from_url(href)
        if not name or not tcin:
            continue
        url = href if href.startswith("http") else f"{base_url}{href}"
        candidates.append(Candidate(name=name, identifier=tcin, url=url, score=0.0))
    return candidates


def _parse_giant_search_results(html: str, base_url: str) -> List[Candidate]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: List[Candidate] = []
    for product in soup.select("a[href*='/grocery/']"):
        name = product.get_text(strip=True)
        href = product.get("href", "")
        if not name or not href:
            continue
        url = href if href.startswith("http") else f"{base_url}{href}"
        slug = href.strip("/").split("/")[-1]
        candidates.append(Candidate(name=name, identifier=slug, url=url, score=0.0))
    return candidates


def _extract_tcin_from_url(url: str) -> Optional[str]:
    parts = url.split("-")
    if parts:
        tail = parts[-1]
        if tail.startswith("A-"):
            return tail.split("A-")[-1]
        if tail.isdigit():
            return tail
    return None

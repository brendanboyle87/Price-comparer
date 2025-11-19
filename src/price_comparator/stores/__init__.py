from __future__ import annotations

from typing import Any

from .base import StoreClient
from .giant import GiantClient
from .target import TargetClient

STORE_CLIENTS = {
    "target": TargetClient,
    "giant": GiantClient,
}


def get_store_client(name: str, **kwargs: Any) -> StoreClient:
    client_cls = STORE_CLIENTS.get(name.lower())
    if not client_cls:
        raise ValueError(f"Unsupported store: {name}")
    return client_cls(**kwargs)

__all__ = ["get_store_client", "TargetClient", "GiantClient", "StoreClient"]

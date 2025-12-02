from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import AppConfig, RawConfig


def load_raw_config(path: str | Path) -> RawConfig:
    data = _load_yaml(path)
    return RawConfig.model_validate(data)


def load_resolved_config(path: str | Path) -> AppConfig:
    data = _load_yaml(path)
    return AppConfig.model_validate(data)


def save_resolved_config(app_config: AppConfig, path: str | Path) -> None:
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        yaml.safe_dump(app_config.model_dump(exclude_none=True), f, sort_keys=False)


def _load_yaml(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PRIMARY_CATALOG_PATH = DATA_DIR / "shl_catalog.json"
FALLBACK_CATALOG_PATH = DATA_DIR / "shl_catalog.sample.json"


@lru_cache(maxsize=1)
def load_catalog() -> list[dict[str, Any]]:
    sources: list[Path] = []
    if PRIMARY_CATALOG_PATH.exists():
        sources.append(PRIMARY_CATALOG_PATH)
    sources.append(FALLBACK_CATALOG_PATH)

    merged: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    seen_urls: set[str] = set()

    for path in sources:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        for item in data:
            if item["name"] in seen_names or item["url"] in seen_urls:
                continue
            merged.append(
                {
                    "name": item["name"],
                    "url": item["url"],
                    "test_type": item["test_type"],
                    "description": item.get("description", ""),
                    "job_levels": item.get("job_levels", []),
                    "languages": item.get("languages", []),
                    "duration_minutes": item.get("duration_minutes"),
                    "remote_testing": bool(item.get("remote_testing", False)),
                    "adaptive": bool(item.get("adaptive", False)),
                    "tags": item.get("tags", []),
                }
            )
            seen_names.add(item["name"])
            seen_urls.add(item["url"])

    return merged

from __future__ import annotations

import json
from pathlib import Path


CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "shl_catalog.json"


def main() -> None:
    if not CATALOG_PATH.exists():
        raise SystemExit("Missing data/shl_catalog.json")

    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if not data:
        raise SystemExit("Catalog exists but is empty")

    names = [item["name"] for item in data]
    urls = [item["url"] for item in data]
    test_types = sorted({item.get("test_type", "") for item in data})

    if len(names) != len(set(names)):
        raise SystemExit("Catalog contains duplicate assessment names")
    if len(urls) != len(set(urls)):
        raise SystemExit("Catalog contains duplicate URLs")
    if any("/product-catalog/view/" not in url for url in urls):
        raise SystemExit("Catalog contains URLs outside the SHL product catalog")

    print(f"Catalog OK: {len(data)} assessments")
    print(f"Test types present: {', '.join(test_types)}")
    print(f"First five assessments: {', '.join(names[:5])}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.shl.com/solutions/products/product-catalog/"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "shl_catalog.json"
CHECKPOINT_PATH = Path(__file__).resolve().parent.parent / "data" / "shl_catalog.checkpoint.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def parse_catalog_page(url: str) -> list[dict]:
    soup = get_soup(url)
    rows = []
    links = soup.select("a[href*='/product-catalog/view/']")
    seen = set()

    for link in links:
        href = link.get("href", "").strip()
        name = link.get_text(" ", strip=True)
        full_url = urljoin(url, href)
        if not name or "/view/" not in full_url:
            continue
        if "solution" in name.lower():
            continue
        if full_url in seen:
            continue
        seen.add(full_url)
        rows.append({"name": name, "url": full_url})
    return rows


def parse_detail(url: str) -> dict:
    soup = get_soup(url)
    text = soup.get_text("\n", strip=True)

    description = ""
    heading = soup.find(string=re.compile(r"Description", re.IGNORECASE))
    if heading and getattr(heading, "parent", None):
        description = heading.parent.get_text(" ", strip=True).replace("Description", "").strip()

    type_match = re.search(r"Test Type:\s*([A-Z])", text)
    duration_match = re.search(r"Approximate Completion Time in minutes\s*=\s*([0-9]+)", text)

    return {
        "description": description,
        "job_levels": [],
        "languages": [],
        "duration_minutes": int(duration_match.group(1)) if duration_match else None,
        "test_type": type_match.group(1) if type_match else "",
        "remote_testing": "Remote Testing" in text,
        "adaptive": "Adaptive/IRT" in text or "adaptive" in text.lower(),
        "tags": [],
    }


def load_existing_checkpoint() -> dict[str, dict]:
    if not CHECKPOINT_PATH.exists():
        return {}
    return {item["url"]: item for item in json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))}


def save_checkpoint(catalog: dict[str, dict]) -> None:
    CHECKPOINT_PATH.write_text(
        json.dumps(sorted(catalog.values(), key=lambda x: x["name"]), indent=2),
        encoding="utf-8",
    )


def discover_catalog(max_start: int, delay_seconds: float) -> dict[str, dict]:
    catalog = load_existing_checkpoint()
    for start in range(0, max_start + 12, 12):
        page_url = f"{BASE_URL}?start={start}&type=1"
        try:
            items = parse_catalog_page(page_url)
        except Exception as exc:
            print(f"Skipping catalog page {page_url}: {exc}")
            continue

        if not items:
            print(f"No items found at {page_url}; stopping discovery.")
            break

        for item in items:
            catalog[item["url"]] = {**catalog.get(item["url"], {}), **item}
        save_checkpoint(catalog)
        print(f"Discovered {len(items)} items from start={start}; running total={len(catalog)}")
        if delay_seconds:
            time.sleep(delay_seconds)
    return catalog


def enrich_catalog(catalog: dict[str, dict], delay_seconds: float) -> list[dict]:
    enriched = []
    for index, item in enumerate(sorted(catalog.values(), key=lambda x: x["name"]), 1):
        try:
            detail = parse_detail(item["url"])
        except Exception as exc:  # pragma: no cover
            print(f"Skipping detail scrape for {item['url']}: {exc}")
            continue
        item.update(detail)
        enriched.append(item)
        if index % 10 == 0:
            print(f"Enriched {index} items")
        if delay_seconds:
            time.sleep(delay_seconds)
    return enriched


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the SHL Individual Test Solutions catalog.")
    parser.add_argument("--max-start", type=int, default=240, help="Maximum pagination start offset to crawl.")
    parser.add_argument("--delay-seconds", type=float, default=0.25, help="Delay between requests.")
    args = parser.parse_args()

    catalog = discover_catalog(max_start=args.max_start, delay_seconds=args.delay_seconds)
    enriched = enrich_catalog(catalog, delay_seconds=args.delay_seconds)

    OUTPUT_PATH.write_text(json.dumps(sorted(enriched, key=lambda x: x["name"]), indent=2), encoding="utf-8")
    print(f"Wrote {len(enriched)} assessments to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

from app.catalog import load_catalog


def test_catalog_has_unique_names_and_urls() -> None:
    catalog = load_catalog()
    assert catalog
    assert len({item["name"] for item in catalog}) == len(catalog)
    assert len({item["url"] for item in catalog}) == len(catalog)


def test_catalog_urls_are_shl_product_catalog_links() -> None:
    catalog = load_catalog()
    for item in catalog:
        assert item["url"].startswith("https://www.shl.com/")
        assert "/product-catalog/view/" in item["url"]

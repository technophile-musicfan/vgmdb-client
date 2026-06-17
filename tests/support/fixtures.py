"""Loader for the committed vgmdb fixture dataset.

Reads the captured HTML and hand-authored golden JSON under ``tests/fixtures/vgmdb/`` and returns
each golden parsed into its M1 model, so a golden that does not fit the schema fails loudly at load
time. The manifest (``manifest.json``) is the source of truth for which fixtures exist.

Parser-vs-golden assertions are **not** part of M5 — they arrive with the parser (M3). This module
only loads the ground truth.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from vgmdb_client.enrich import AlbumEnrichment
from vgmdb_client.models import Album, Artist, Organization, Product, SearchResults

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "vgmdb"
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"
ALBUMS_DIR = FIXTURES_DIR / "albums"
SEARCH_DIR = FIXTURES_DIR / "search"
ARTISTS_DIR = FIXTURES_DIR / "artists"
PRODUCTS_DIR = FIXTURES_DIR / "products"
ORGANIZATIONS_DIR = FIXTURES_DIR / "organizations"
ENRICHMENT_DIR = FIXTURES_DIR / "enrichment"


def load_manifest() -> dict[str, Any]:
    """Return the parsed fixture manifest."""
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def iter_album_fixtures() -> Iterator[int]:
    """Yield every album id recorded in the manifest."""
    for entry in load_manifest().get("albums", []):
        yield int(entry["id"])


def iter_search_fixtures() -> Iterator[str]:
    """Yield every search slug recorded in the manifest."""
    for entry in load_manifest().get("search", []):
        yield str(entry["slug"])


def _iter_captured_ids(section: str) -> Iterator[int]:
    """Yield ids of manifest entries in ``section`` that have been captured."""
    for entry in load_manifest().get(section, []):
        if entry.get("status") == "captured":
            yield int(entry["id"])


def iter_artist_fixtures() -> Iterator[int]:
    """Yield every captured artist id recorded in the manifest."""
    yield from _iter_captured_ids("artists")


def iter_product_fixtures() -> Iterator[int]:
    """Yield every captured product id recorded in the manifest."""
    yield from _iter_captured_ids("products")


def iter_organization_fixtures() -> Iterator[int]:
    """Yield every captured organization id recorded in the manifest."""
    yield from _iter_captured_ids("organizations")


def iter_enrichment_goldens() -> Iterator[int]:
    """Yield every album id that has a committed enrichment golden."""
    for path in sorted(ENRICHMENT_DIR.glob("*.json"), key=lambda p: int(p.stem)):
        yield int(path.stem)


def load_album_fixture(album_id: int) -> tuple[str, Album]:
    """Return ``(raw_html, golden_album)`` for an album fixture.

    The golden JSON is validated against the :class:`Album` model on load.
    """
    html = (ALBUMS_DIR / f"{album_id}.html").read_text(encoding="utf-8")
    golden = (ALBUMS_DIR / f"{album_id}.json").read_text(encoding="utf-8")
    return html, Album.model_validate_json(golden)


def load_search_fixture(slug: str) -> tuple[str, SearchResults]:
    """Return ``(raw_html, golden_results)`` for a search fixture.

    The golden JSON is validated against the :class:`SearchResults` model on load.
    """
    html = (SEARCH_DIR / f"{slug}.html").read_text(encoding="utf-8")
    golden = (SEARCH_DIR / f"{slug}.json").read_text(encoding="utf-8")
    return html, SearchResults.model_validate_json(golden)


def load_enrichment_golden(album_id: int) -> AlbumEnrichment:
    """Return the hand-authored enrichment golden for an album (validated on load)."""
    golden = (ENRICHMENT_DIR / f"{album_id}.json").read_text(encoding="utf-8")
    return AlbumEnrichment.model_validate_json(golden)


def load_artist_fixture(artist_id: int) -> tuple[str, Artist]:
    """Return ``(raw_html, golden_artist)`` for an artist fixture (golden validated on load)."""
    html = (ARTISTS_DIR / f"{artist_id}.html").read_text(encoding="utf-8")
    golden = (ARTISTS_DIR / f"{artist_id}.json").read_text(encoding="utf-8")
    return html, Artist.model_validate_json(golden)


def load_product_fixture(product_id: int) -> tuple[str, Product]:
    """Return ``(raw_html, golden_product)`` for a product fixture (golden validated on load)."""
    html = (PRODUCTS_DIR / f"{product_id}.html").read_text(encoding="utf-8")
    golden = (PRODUCTS_DIR / f"{product_id}.json").read_text(encoding="utf-8")
    return html, Product.model_validate_json(golden)


def load_organization_fixture(org_id: int) -> tuple[str, Organization]:
    """Return ``(raw_html, golden_org)`` for an organization fixture (golden validated on load)."""
    html = (ORGANIZATIONS_DIR / f"{org_id}.html").read_text(encoding="utf-8")
    golden = (ORGANIZATIONS_DIR / f"{org_id}.json").read_text(encoding="utf-8")
    return html, Organization.model_validate_json(golden)

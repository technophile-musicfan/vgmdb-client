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

from vgmdb_client.models import Album, SearchResults

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "vgmdb"
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"
ALBUMS_DIR = FIXTURES_DIR / "albums"
SEARCH_DIR = FIXTURES_DIR / "search"


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

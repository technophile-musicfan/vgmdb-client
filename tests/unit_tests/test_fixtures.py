"""Well-formedness tests for the vgmdb fixture dataset (M5).

These assert the dataset is internally consistent and that every golden validates against its M1
model. Parser-vs-golden assertions are NOT part of M5 — they arrive with the parser (M3).

Until the seed HTML is captured (G3) and golden authored (G4), the four ``test_all_manifest_*``
completeness tests fail by design, listing exactly what is still pending. Every other test holds
both before and after capture.
"""

from __future__ import annotations

from pathlib import Path

from tests.support.fixtures import (
    ALBUMS_DIR,
    SEARCH_DIR,
    iter_album_fixtures,
    iter_search_fixtures,
    load_album_fixture,
    load_manifest,
    load_search_fixture,
)
from vgmdb_client.models import Album, SearchResults

MIN_ALBUMS = 10
MIN_SEARCH = 2


def _nonempty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


# --- manifest shape (holds before and after capture) ---------------------------------------


def test_manifest_meets_minimum_dataset_size() -> None:
    manifest = load_manifest()
    assert len(manifest["albums"]) >= MIN_ALBUMS
    assert len(manifest["search"]) >= MIN_SEARCH


def test_manifest_album_entries_are_well_formed() -> None:
    for entry in load_manifest()["albums"]:
        assert isinstance(entry["id"], int)
        assert entry["kind"] == "album"
        assert entry["source_url"]
        assert entry["diversity"], f"album {entry['id']} has no diversity tags"


def test_manifest_search_entries_are_well_formed() -> None:
    for entry in load_manifest()["search"]:
        assert entry["slug"]
        assert entry["query"]
        assert entry["kind"] == "search"
        assert entry["source_url"]
        assert entry["diversity"], f"search {entry['slug']} has no diversity tags"


def test_manifest_album_ids_are_unique() -> None:
    ids = list(iter_album_fixtures())
    assert len(ids) == len(set(ids))


def test_manifest_search_slugs_are_unique() -> None:
    slugs = list(iter_search_fixtures())
    assert len(slugs) == len(set(slugs))


# --- no orphan files: anything on disk must be in the manifest (holds before capture) -------


def test_no_orphan_album_files() -> None:
    manifest_ids = {str(i) for i in iter_album_fixtures()}
    on_disk = {p.stem for p in ALBUMS_DIR.glob("*.html")} | {p.stem for p in ALBUMS_DIR.glob("*.json")}
    orphans = on_disk - manifest_ids
    assert not orphans, f"album files with no manifest entry: {sorted(orphans)}"


def test_no_orphan_search_files() -> None:
    manifest_slugs = set(iter_search_fixtures())
    on_disk = {p.stem for p in SEARCH_DIR.glob("*.html")} | {p.stem for p in SEARCH_DIR.glob("*.json")}
    orphans = on_disk - manifest_slugs
    assert not orphans, f"search files with no manifest entry: {sorted(orphans)}"


# --- every golden present on disk validates against its M1 model (grows as goldens land) ----


def test_existing_album_goldens_validate() -> None:
    for golden in sorted(ALBUMS_DIR.glob("*.json")):
        Album.model_validate_json(golden.read_text(encoding="utf-8"))


def test_existing_search_goldens_validate() -> None:
    for golden in sorted(SEARCH_DIR.glob("*.json")):
        SearchResults.model_validate_json(golden.read_text(encoding="utf-8"))


def test_loader_roundtrips_existing_albums() -> None:
    for golden in sorted(ALBUMS_DIR.glob("*.json")):
        album_id = int(golden.stem)
        if not _nonempty(ALBUMS_DIR / f"{album_id}.html"):
            continue
        html, album = load_album_fixture(album_id)
        assert isinstance(html, str) and html
        assert isinstance(album, Album)


def test_loader_roundtrips_existing_search() -> None:
    for golden in sorted(SEARCH_DIR.glob("*.json")):
        slug = golden.stem
        if not _nonempty(SEARCH_DIR / f"{slug}.html"):
            continue
        html, results = load_search_fixture(slug)
        assert isinstance(html, str) and html
        assert isinstance(results, SearchResults)


# --- dataset completeness: RED until capture (G3) + golden authoring (G4) -------------------


def test_all_manifest_albums_have_nonempty_html() -> None:
    missing = [i for i in iter_album_fixtures() if not _nonempty(ALBUMS_DIR / f"{i}.html")]
    assert not missing, (
        f"album HTML not yet captured for ids {missing}; run `uv run python scripts/capture_fixtures.py` (G3)"
    )


def test_all_manifest_search_have_nonempty_html() -> None:
    missing = [s for s in iter_search_fixtures() if not _nonempty(SEARCH_DIR / f"{s}.html")]
    assert not missing, (
        f"search HTML not yet captured for slugs {missing}; run `uv run python scripts/capture_fixtures.py` (G3)"
    )


def test_all_manifest_albums_have_golden() -> None:
    missing = [i for i in iter_album_fixtures() if not _nonempty(ALBUMS_DIR / f"{i}.json")]
    assert not missing, f"golden Album JSON not yet authored for ids {missing} (G4)"


def test_all_manifest_search_have_golden() -> None:
    missing = [s for s in iter_search_fixtures() if not _nonempty(SEARCH_DIR / f"{s}.json")]
    assert not missing, f"golden SearchResults JSON not yet authored for slugs {missing} (G4)"

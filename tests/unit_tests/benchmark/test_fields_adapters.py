"""Tests for the canonical record: normalizer + the three adapters."""

from __future__ import annotations

from benchmarks.quality.adapters import from_album, from_golden, from_hufman
from benchmarks.quality.fields import normalize, track_field
from tests.support.fixtures import load_album_fixture


def test_normalize_collapses_whitespace_and_casefolds() -> None:
    assert normalize("  Perfect   Dark  ") == "perfect dark"
    assert normalize("MiXeD") == "mixed"
    assert normalize(None) is None
    assert normalize("   ") is None


def test_track_field_path() -> None:
    assert track_field(1, 1) == "disc1.track1.title"
    assert track_field(2, 13) == "disc2.track13.title"


def test_from_album_reduces_golden() -> None:
    _, golden = load_album_fixture(271)
    record = from_album(golden)
    assert record["title"] == "Perfect Dark Zero Original Soundtrack"
    assert record["catalog"] == "SE-2020-2"
    assert record["release_date"] == "2005-11-08"
    assert record["classification"] == "Original Soundtrack, Vocal"
    assert record["disc1.track1.title"] == "Perfect Dark Zero - Title"


def test_from_golden_produces_expected_record() -> None:
    _, golden = load_album_fixture(271)
    record = from_golden(golden)
    # Pin the golden adapter's output explicitly (not just equality to from_album).
    assert record["title"] == "Perfect Dark Zero Original Soundtrack"
    assert record["catalog"] == "SE-2020-2"
    assert record["release_date"] == "2005-11-08"
    assert record["disc1.track1.title"] == "Perfect Dark Zero - Title"


def test_from_hufman_tolerant_of_missing_fields() -> None:
    # Empty payload: every field maps to None, no error raised.
    record = from_hufman({})
    assert record == {"title": None, "catalog": None, "release_date": None, "classification": None}


def test_from_hufman_extracts_known_shape() -> None:
    data = {
        "name": "Perfect Dark Zero Original Soundtrack",
        "catalog": "SE-2020-2",
        "release_date": "2005-11-08",
        "classification": "Original Soundtrack",
        "discs": [{"name": "Disc 1", "tracks": [{"names": {"English": "Perfect Dark Zero - Title"}}]}],
    }
    record = from_hufman(data)
    assert record["title"] == "Perfect Dark Zero Original Soundtrack"
    assert record["catalog"] == "SE-2020-2"
    assert record["disc1.track1.title"] == "Perfect Dark Zero - Title"


def test_from_hufman_name_mapping_and_missing_catalog() -> None:
    # title from a names mapping (no "name"); catalog absent -> None (tolerant).
    data = {"names": {"Japanese": "タイトル", "English": "Title"}}
    record = from_hufman(data)
    assert record["title"] == "Title"
    assert record["catalog"] is None

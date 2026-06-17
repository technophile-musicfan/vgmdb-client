"""Tests for the deterministic RuleBasedBackend enrichment extractor."""

from __future__ import annotations

import pytest

from benchmarks.quality.enrichment import score_enrichment
from tests.support.fixtures import iter_enrichment_goldens, load_album_fixture, load_enrichment_golden
from vgmdb_client.enrich import RuleBasedBackend
from vgmdb_client.enrich.rules import _parse_track_set
from vgmdb_client.models import Album, Disc, LocalizedText, Role, Track


def _album(n_tracks: int, notes: str) -> Album:
    tracks = [Track(titles=LocalizedText({"English": f"T{i}"}), number=i) for i in range(1, n_tracks + 1)]
    return Album(id=1, titles=LocalizedText({"English": "A"}), discs=[Disc(number=1, tracks=tracks)], notes=notes)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1,4,5", {1, 4, 5}),
        ("1~3", {1, 2, 3}),
        ("01, 07", {1, 7}),
        ("M-01", {1}),
        ("M01~12, 14~23, 27~31", {*range(1, 13), *range(14, 24), *range(27, 32)}),
        ("no digits here", set()),
    ],
)
def test_parse_track_set(text: str, expected: set[int]) -> None:
    assert _parse_track_set(text) == expected


def test_block_pattern_attributes_role_to_range_header() -> None:
    album = _album(5, "Tracks 1,4,5\nComposed & Arranged by SHOGUN")
    enrichment = RuleBasedBackend().enrich(album, album.notes or "")
    assert set(enrichment.track_credits) == {1, 4, 5}
    credit = enrichment.track_credits[1][0]
    assert credit.role is Role.COMPOSER
    assert credit.artists[0].names.default == "SHOGUN"


def test_inline_parenthetical_attributes_names_to_ranges() -> None:
    album = _album(3, "Composition: Nobuo Uematsu (1~3)\nArrangement: Almighty Associates (1~2), Shiro Hamaguchi (3)")
    enrichment = RuleBasedBackend().enrich(album, album.notes or "")
    assert enrichment.track_credits[1][0].artists[0].names.default == "Nobuo Uematsu"
    # track 3's arranger differs from tracks 1-2's
    assert enrichment.track_credits[3][-1].artists[0].names.default == "Shiro Hamaguchi"
    assert enrichment.track_credits[2][-1].artists[0].names.default == "Almighty Associates"


def test_multi_artist_names_split() -> None:
    album = _album(1, "1.\nPerformed by Kepi and Kat")
    enrichment = RuleBasedBackend().enrich(album, album.notes or "")
    names = {a.names.default for a in enrichment.track_credits[1][0].artists}
    assert names == {"Kepi", "Kat"}


def test_album_level_credit_without_track_reference_is_dropped() -> None:
    # No track header / no inline range -> nothing emitted (precision safeguard).
    album = _album(3, "All Music Composed, Arranged & Produced by: Yasunori Mitsuda")
    enrichment = RuleBasedBackend().enrich(album, album.notes or "")
    assert enrichment.is_empty


def test_backend_conforms_to_protocol() -> None:
    from vgmdb_client.enrich import EnrichmentBackend, enrich_album

    backend: EnrichmentBackend = RuleBasedBackend()  # structural typing check
    _, album = load_album_fixture(10000)
    assert enrich_album(album, backend).track_credits  # routed through the helper


# --- golden-scored: measured against the Cycle 1 enrichment goldens -----------------------


def _score(album_id: int) -> tuple[float, float]:
    _, album = load_album_fixture(album_id)
    produced = RuleBasedBackend().enrich(album, album.notes or "")
    s = score_enrichment(produced, load_enrichment_golden(album_id))
    return s.recall, s.precision


@pytest.mark.parametrize("album_id", [10000, 22000])
def test_high_recall_and_precision_on_clean_albums(album_id: int) -> None:
    recall, precision = _score(album_id)
    assert recall == 1.0
    assert precision == 1.0


@pytest.mark.parametrize("album_id", [4, 5012, 30000, 60000])
def test_no_hallucination_on_empty_goldens(album_id: int) -> None:
    _, album = load_album_fixture(album_id)
    produced = RuleBasedBackend().enrich(album, album.notes or "")
    assert produced.is_empty  # nothing extracted where the golden is empty
    assert _score(album_id)[1] == 1.0  # precision 1.0


def test_aggregate_recall_is_reasonable() -> None:
    matched = produced = golden = 0
    for album_id in iter_enrichment_goldens():
        _, album = load_album_fixture(album_id)
        s = score_enrichment(RuleBasedBackend().enrich(album, album.notes or ""), load_enrichment_golden(album_id))
        matched += s.matched
        produced += s.produced
        golden += s.golden
    assert matched / golden > 0.7  # conservative baseline still recovers most credits
    assert matched / produced > 0.85  # and stays precise

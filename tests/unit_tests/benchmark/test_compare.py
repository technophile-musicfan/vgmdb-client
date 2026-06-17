"""Tests for per-field scoring, agreement, and enrichment coverage."""

from __future__ import annotations

from benchmarks.quality.compare import (
    ABSENT,
    EXTRA,
    MATCH,
    MISMATCH,
    MISSING,
    agreement,
    coverage_for,
    score_record,
)
from vgmdb_client.enrich import AlbumEnrichment
from vgmdb_client.models import Album, Credit, Disc, LocalizedText, Role, Track


def _status(scores: list, field: str) -> str:
    return next(s.status for s in scores if s.field == field)


def test_score_record_covers_all_outcomes() -> None:
    golden = {"title": "Album A", "catalog": "CAT-1", "release_date": "2005"}
    source = {"title": "album a", "catalog": "CAT-2", "classification": "Game"}
    scores = score_record(source, golden)
    assert _status(scores, "title") == MATCH  # casefold-equal
    assert _status(scores, "catalog") == MISMATCH
    assert _status(scores, "release_date") == MISSING  # golden has it, source doesn't
    assert _status(scores, "classification") == EXTRA  # source has it, golden doesn't


def test_score_record_both_absent_is_absent() -> None:
    scores = score_record({"title": None}, {"title": None})
    assert _status(scores, "title") == ABSENT


def test_agreement_counts_only_golden_present_fields() -> None:
    golden = {"title": "A", "catalog": "C", "release_date": "2005"}
    source = {"title": "A", "catalog": "X", "classification": "Game"}  # match, mismatch, missing, extra
    matches, scored = agreement(score_record(source, golden))
    assert (matches, scored) == (1, 3)  # extra not counted in denominator


def _album_with_tracks(n: int) -> Album:
    tracks = [Track(titles=LocalizedText({"English": f"T{i}"}), number=i) for i in range(1, n + 1)]
    return Album(id=1, titles=LocalizedText({"English": "A"}), discs=[Disc(number=1, tracks=tracks)])


def test_coverage_no_backend() -> None:
    cov = coverage_for(_album_with_tracks(2), None)
    assert cov.available is False


def test_coverage_with_enrichment() -> None:
    album = _album_with_tracks(3)
    enrichment = AlbumEnrichment(
        album_id=1,
        track_credits={1: [Credit(role=Role.COMPOSER, role_raw="Music")], 2: []},
    )
    cov = coverage_for(album, enrichment)
    assert cov.available is True
    assert cov.total_tracks == 3
    assert cov.tracks_with_credits == 1  # track 2's empty list doesn't count
    assert cov.total_credits == 1


def test_coverage_ignores_credits_for_nonexistent_tracks() -> None:
    # A credit keyed to a track number the album doesn't have must not inflate the fraction.
    album = _album_with_tracks(2)  # track numbers 1, 2
    enrichment = AlbumEnrichment(
        album_id=1,
        track_credits={1: [Credit(role=Role.COMPOSER, role_raw="Music")], 99: [Credit(role=Role.OTHER, role_raw="?")]},
    )
    cov = coverage_for(album, enrichment)
    assert cov.total_tracks == 2
    assert cov.tracks_with_credits == 1  # track 99 doesn't exist -> excluded
    assert cov.total_credits == 1

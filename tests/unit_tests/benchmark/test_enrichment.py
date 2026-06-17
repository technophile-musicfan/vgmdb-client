"""Tests for the enrichment credit-matching scorer (precision / recall / F1)."""

from __future__ import annotations

import pytest

from benchmarks.quality.enrichment import score_enrichment
from vgmdb_client.enrich import AlbumEnrichment
from vgmdb_client.models import ArtistRef, Credit, LocalizedText, Role


def _credit(role: Role, *names: str) -> Credit:
    return Credit(
        role=role,
        role_raw=role.value,
        artists=[ArtistRef(names=LocalizedText({"English": n})) for n in names],
    )


def _enr(track_credits: dict[int, list[Credit]]) -> AlbumEnrichment:
    return AlbumEnrichment(album_id=1, track_credits=track_credits)


def test_exact_match_is_perfect() -> None:
    golden = _enr({1: [_credit(Role.COMPOSER, "A")]})
    score = score_enrichment(golden, golden)
    assert (score.precision, score.recall, score.f1) == (1.0, 1.0, 1.0)


def test_empty_vs_empty_is_perfect() -> None:
    score = score_enrichment(_enr({}), _enr({}))
    assert (score.precision, score.recall, score.f1) == (1.0, 1.0, 1.0)


def test_hallucination_against_empty_golden() -> None:
    score = score_enrichment(_enr({1: [_credit(Role.COMPOSER, "A")]}), _enr({}))
    assert score.recall == 1.0  # nothing to find
    assert score.precision == 0.0  # produced a false credit


def test_partial_recall() -> None:
    golden = _enr({1: [_credit(Role.COMPOSER, "A"), _credit(Role.ARRANGER, "B")]})
    produced = _enr({1: [_credit(Role.COMPOSER, "A")]})
    score = score_enrichment(produced, golden)
    assert score.precision == 1.0
    assert score.recall == 0.5
    assert score.f1 == pytest.approx(2 * 1.0 * 0.5 / 1.5)


def test_role_mismatch_does_not_match() -> None:
    golden = _enr({1: [_credit(Role.COMPOSER, "A")]})
    produced = _enr({1: [_credit(Role.ARRANGER, "A")]})  # same artist + track, different role
    score = score_enrichment(produced, golden)
    assert score.recall == 0.0 and score.precision == 0.0


def test_artist_name_overlap_matches() -> None:
    golden = _enr({1: [_credit(Role.COMPOSER, "Alice", "Bob")]})
    produced = _enr({1: [_credit(Role.COMPOSER, "bob")]})  # casefolded overlap on "bob"
    score = score_enrichment(produced, golden)
    assert score.recall == 1.0 and score.precision == 1.0


def test_wrong_track_does_not_match() -> None:
    golden = _enr({1: [_credit(Role.COMPOSER, "A")]})
    produced = _enr({2: [_credit(Role.COMPOSER, "A")]})  # right credit, wrong track
    score = score_enrichment(produced, golden)
    assert score.recall == 0.0 and score.precision == 0.0

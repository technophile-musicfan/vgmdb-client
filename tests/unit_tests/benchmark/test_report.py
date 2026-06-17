"""Tests for Markdown/stdout rendering of comparisons."""

from __future__ import annotations

from benchmarks.quality.compare import (
    HUFMAN,
    OURS,
    AlbumComparison,
    Coverage,
    score_record,
)
from benchmarks.quality.report import render_markdown, render_summary, source_names


def _comparison(*, with_hufman: bool, coverage: Coverage) -> AlbumComparison:
    golden = {"title": "Album A", "catalog": "CAT-1"}
    sources = {OURS: {"title": "Album A", "catalog": "CAT-2"}}
    if with_hufman:
        sources[HUFMAN] = {"title": "Album A", "catalog": "CAT-1"}
    scores = {name: score_record(rec, golden) for name, rec in sources.items()}
    return AlbumComparison(
        album_id=271, title="Album A", golden=golden, sources=sources, scores=scores, coverage=coverage
    )


def test_source_names_first_seen_order() -> None:
    comparisons = [_comparison(with_hufman=True, coverage=Coverage(available=False))]
    assert source_names(comparisons) == [OURS, HUFMAN]


def test_markdown_has_all_sections_and_hufman_note_when_absent() -> None:
    comparisons = [_comparison(with_hufman=False, coverage=Coverage(available=False))]
    md = render_markdown(comparisons)
    assert "# Parsing-quality report" in md
    assert "## Scorecard" in md
    assert "## Enrichment coverage (ours+LLM)" in md
    assert "## Per-album field detail" in md
    assert "hufman column omitted" in md  # hufman absent -> caveat shown
    assert "n/a (no backend)" in md
    assert "Album 271" in md


def test_markdown_reports_hufman_column_and_coverage_when_present() -> None:
    cov = Coverage(available=True, tracks_with_credits=2, total_tracks=5, total_credits=3)
    comparisons = [_comparison(with_hufman=True, coverage=cov)]
    md = render_markdown(comparisons)
    assert "hufman column omitted" not in md
    assert HUFMAN in md
    assert "2/5 tracks, 3 credits" in md


def test_summary_contains_scorecard_and_coverage() -> None:
    comparisons = [_comparison(with_hufman=False, coverage=Coverage(available=False))]
    summary = render_summary(comparisons)
    assert "Field agreement vs golden" in summary
    assert OURS in summary
    assert "album 271" in summary

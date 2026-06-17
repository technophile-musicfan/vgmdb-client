"""Tests for Markdown/stdout rendering of comparisons."""

from __future__ import annotations

from benchmarks.quality.compare import (
    HUFMAN,
    OURS,
    AlbumComparison,
    Coverage,
    EnrichmentEntry,
    score_record,
)
from benchmarks.quality.enrichment import EnrichmentScore
from benchmarks.quality.report import backend_names, render_markdown, render_summary, source_names


def _comparison(*, with_hufman: bool, enrichment: dict[str, EnrichmentEntry] | None = None) -> AlbumComparison:
    golden = {"title": "Album A", "catalog": "CAT-1"}
    sources = {OURS: {"title": "Album A", "catalog": "CAT-2"}}
    if with_hufman:
        sources[HUFMAN] = {"title": "Album A", "catalog": "CAT-1"}
    scores = {name: score_record(rec, golden) for name, rec in sources.items()}
    return AlbumComparison(
        album_id=271, title="Album A", golden=golden, sources=sources, scores=scores, enrichment=enrichment or {}
    )


def _entry(matched: int, produced: int, golden: int) -> EnrichmentEntry:
    return EnrichmentEntry(
        coverage=Coverage(available=True, tracks_with_credits=matched, total_tracks=5, total_credits=produced),
        score=EnrichmentScore(matched=matched, produced=produced, golden=golden),
    )


def test_source_names_first_seen_order() -> None:
    comparisons = [_comparison(with_hufman=True)]
    assert source_names(comparisons) == [OURS, HUFMAN]


def test_markdown_has_all_sections_and_hufman_note_when_absent() -> None:
    comparisons = [_comparison(with_hufman=False)]
    md = render_markdown(comparisons)
    assert "# Parsing-quality report" in md
    assert "## Scorecard" in md
    assert "## Enrichment quality" in md
    assert "## Per-album field detail" in md
    assert "hufman column omitted" in md  # hufman absent -> caveat shown
    assert "No enrichment backends configured." in md
    assert "Album 271" in md


def test_markdown_ranks_named_backends() -> None:
    comparisons = [_comparison(with_hufman=False, enrichment={"llm": _entry(2, 2, 2), "rule": _entry(1, 3, 2)})]
    md = render_markdown(comparisons)
    assert backend_names(comparisons) == ["llm", "rule"]
    assert "| llm | 1.00 | 1.00 | 1.00" in md  # perfect
    assert "| rule | 0.33 | 0.50 | 0.40" in md  # 1/3 precision, 1/2 recall


def test_summary_reports_scorecard_and_enrichment() -> None:
    comparisons = [_comparison(with_hufman=False, enrichment={"llm": _entry(2, 2, 2)})]
    summary = render_summary(comparisons)
    assert "Field agreement vs golden" in summary
    assert OURS in summary
    assert "Enrichment quality vs golden" in summary
    assert "llm" in summary


def test_summary_no_backends() -> None:
    summary = render_summary([_comparison(with_hufman=False)])
    assert "no backends configured" in summary

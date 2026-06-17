"""End-to-end smoke test: the harness runs over the fixtures with no Docker and no live LLM."""

from __future__ import annotations

from pathlib import Path

from benchmarks.quality.compare import OURS
from benchmarks.quality.run import run
from tests.support.fixtures import iter_album_fixtures, load_enrichment_golden
from vgmdb_client.enrich import AlbumEnrichment
from vgmdb_client.models import Album


class GoldenBackend:
    """A perfect backend: returns the album's enrichment golden verbatim."""

    def enrich(self, album: Album, raw_text: str) -> AlbumEnrichment:
        return load_enrichment_golden(album.id)


class EmptyBackend:
    """A backend that extracts nothing."""

    def enrich(self, album: Album, raw_text: str) -> AlbumEnrichment:
        return AlbumEnrichment(album_id=album.id)


def test_harness_runs_without_hufman_or_backends(tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    comparisons = run(report_path=report_path, hufman_enabled=False, backends={})

    assert len(comparisons) == len(list(iter_album_fixtures()))
    assert all(OURS in c.sources for c in comparisons)
    assert all(not c.enrichment for c in comparisons)

    report = report_path.read_text(encoding="utf-8")
    assert "## Scorecard" in report
    assert "hufman column omitted" in report  # hufman disabled -> dropped, run still completes
    assert "No enrichment backends configured." in report
    assert f"| {OURS} |" in report


def test_harness_scores_named_backends(tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    comparisons = run(
        report_path=report_path,
        hufman_enabled=False,
        backends={"perfect": GoldenBackend(), "empty": EmptyBackend()},
    )
    by_id = {c.album_id: c for c in comparisons}

    # Album 271 has a populated enrichment golden (tracks 10/11/27).
    perfect = by_id[271].enrichment["perfect"].score
    assert perfect.recall == 1.0 and perfect.precision == 1.0
    # The empty backend finds nothing on a populated album: recall 0, but precision 1 (no false positives).
    empty = by_id[271].enrichment["empty"].score
    assert empty.recall == 0.0 and empty.precision == 1.0

    report = report_path.read_text(encoding="utf-8")
    assert "## Enrichment quality" in report
    assert "perfect" in report and "empty" in report

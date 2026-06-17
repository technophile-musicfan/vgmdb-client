"""End-to-end smoke test: the harness runs over the fixtures with no Docker and no LLM backend."""

from __future__ import annotations

from pathlib import Path

from benchmarks.quality.compare import OURS
from benchmarks.quality.run import run
from tests.support.fixtures import iter_album_fixtures


def test_harness_runs_over_fixtures_without_hufman_or_backend(tmp_path: Path) -> None:
    report_path = tmp_path / "report.md"
    comparisons = run(report_path=report_path, hufman_enabled=False, backend=None)

    # One comparison per album fixture; ours scored against golden; no enrichment (no backend).
    assert len(comparisons) == len(list(iter_album_fixtures()))
    assert all(OURS in c.sources for c in comparisons)
    assert all(c.coverage.available is False for c in comparisons)

    report = report_path.read_text(encoding="utf-8")
    assert "## Scorecard" in report
    assert "hufman column omitted" in report  # hufman disabled -> dropped, run still completes
    assert f"| {OURS} |" in report

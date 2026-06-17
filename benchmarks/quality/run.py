"""Entry point: run the quality harness over the album fixtures and emit the report.

Usage (dev-only)::

    uv run python -m benchmarks.quality.run

Config via env: ``HUFMAN_URL`` (default ``http://localhost:5000``) for the hufman column, and
``LLM_URL`` / ``LLM_MODEL`` / ``LLM_API_KEY`` (via ``backend_from_env``) for the ours+LLM coverage.
"""

from __future__ import annotations

from pathlib import Path

from benchmarks.quality.adapters import from_album, from_golden, from_hufman
from benchmarks.quality.compare import (
    HUFMAN,
    OURS,
    AlbumComparison,
    EnrichmentEntry,
    coverage_for,
    score_record,
)
from benchmarks.quality.enrichment import score_enrichment
from benchmarks.quality.hufman_client import fetch_album
from benchmarks.quality.report import render_markdown, render_summary
from tests.support.fixtures import iter_album_fixtures, load_album_fixture, load_enrichment_golden
from vgmdb_client.enrich import EnrichmentBackend, backend_from_env, enrich_album
from vgmdb_client.parsers import parse_album

DEFAULT_REPORT_PATH = Path(__file__).resolve().parent / "report.md"


def run(
    *,
    report_path: Path = DEFAULT_REPORT_PATH,
    hufman_enabled: bool = True,
    backends: dict[str, EnrichmentBackend] | None = None,
) -> list[AlbumComparison]:
    """Compare every album fixture, write the Markdown report, print the summary, return comparisons.

    ``backends`` is a mapping of label -> enrichment backend; each is scored against the album's
    enrichment golden so the report ranks them. With no backends, only structural scoring is reported.
    """
    backends = backends or {}
    comparisons: list[AlbumComparison] = []
    for album_id in iter_album_fixtures():
        html, golden = load_album_fixture(album_id)
        ours = parse_album(html)
        golden_record = from_golden(golden)

        sources = {OURS: from_album(ours)}
        if hufman_enabled:
            data = fetch_album(album_id)
            if data is not None:
                sources[HUFMAN] = from_hufman(data)

        scores = {name: score_record(record, golden_record) for name, record in sources.items()}

        enrichment_golden = load_enrichment_golden(album_id)
        enrichment: dict[str, EnrichmentEntry] = {}
        for label, backend in backends.items():
            produced = enrich_album(ours, backend)
            enrichment[label] = EnrichmentEntry(
                coverage=coverage_for(ours, produced),
                score=score_enrichment(produced, enrichment_golden),
            )

        comparisons.append(
            AlbumComparison(
                album_id=album_id,
                title=ours.titles.default,
                golden=golden_record,
                sources=sources,
                scores=scores,
                enrichment=enrichment,
            )
        )

    report_path.write_text(render_markdown(comparisons), encoding="utf-8")
    print(render_summary(comparisons))
    print(f"\nReport written to {report_path}")
    return comparisons


def main() -> None:
    """CLI entry point: hufman + LLM backend driven entirely by the environment."""
    backend = backend_from_env()
    run(hufman_enabled=True, backends={"llm": backend} if backend is not None else {})


if __name__ == "__main__":
    main()

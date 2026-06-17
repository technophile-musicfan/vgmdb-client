"""Render the quality report (Markdown) and the stdout summary from album comparisons."""

from __future__ import annotations

from benchmarks.quality.compare import HUFMAN, AlbumComparison, FieldScore, agreement
from benchmarks.quality.enrichment import EnrichmentScore

# Short markers for per-field status in the detail tables.
_STATUS_MARK = {
    "match": "=",
    "mismatch": "x",
    "missing": "-",
    "extra": "+",
    "absent": " ",
}


def source_names(comparisons: list[AlbumComparison]) -> list[str]:
    """Source labels present across the comparisons, in first-seen order (e.g. ours, hufman)."""
    names: list[str] = []
    for comparison in comparisons:
        for name in comparison.sources:
            if name not in names:
                names.append(name)
    return names


def _pct(matches: int, scored: int) -> str:
    return f"{100.0 * matches / scored:.0f}%" if scored else "n/a"


def _scorecard_rows(comparisons: list[AlbumComparison], names: list[str]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for name in names:
        total_matches = 0
        total_scored = 0
        for comparison in comparisons:
            scores = comparison.scores.get(name)
            if scores is None:
                continue
            matches, scored = agreement(scores)
            total_matches += matches
            total_scored += scored
        rows.append((name, _pct(total_matches, total_scored), f"{total_matches}/{total_scored}"))
    return rows


def backend_names(comparisons: list[AlbumComparison]) -> list[str]:
    """Enrichment backend labels present across the comparisons, in first-seen order."""
    names: list[str] = []
    for comparison in comparisons:
        for name in comparison.enrichment:
            if name not in names:
                names.append(name)
    return names


def _aggregate_enrichment(comparisons: list[AlbumComparison], backend: str) -> EnrichmentScore:
    """Sum a backend's matched/produced/golden counts across all albums into one score."""
    matched = produced = golden = 0
    for comparison in comparisons:
        entry = comparison.enrichment.get(backend)
        if entry is None:
            continue
        matched += entry.score.matched
        produced += entry.score.produced
        golden += entry.score.golden
    return EnrichmentScore(matched=matched, produced=produced, golden=golden)


def render_summary(comparisons: list[AlbumComparison]) -> str:
    """A compact scorecard + enrichment-quality summary for stdout."""
    names = source_names(comparisons)
    lines = ["Parsing-quality summary", "  Field agreement vs golden:"]
    for name, pct, ratio in _scorecard_rows(comparisons, names):
        lines.append(f"    {name:<8} {pct:>5}  ({ratio})")
    backends = backend_names(comparisons)
    if backends:
        lines.append("  Enrichment quality vs golden:")
        for backend in backends:
            agg = _aggregate_enrichment(comparisons, backend)
            lines.append(
                f"    {backend:<8} P {agg.precision:.2f} / R {agg.recall:.2f} / F1 {agg.f1:.2f}"
                f"  ({agg.matched}/{agg.golden} found, {agg.produced} produced)"
            )
    else:
        lines.append("  Enrichment: no backends configured.")
    return "\n".join(lines)


def _detail_table(comparison: AlbumComparison, names: list[str]) -> list[str]:
    present = [n for n in names if n in comparison.sources]
    header = "| field | golden | " + " | ".join(present) + " |"
    sep = "|" + "---|" * (2 + len(present))
    lines = [header, sep]
    paths = list(comparison.golden)
    for name in present:
        for score in comparison.scores[name]:
            if score.field not in paths:
                paths.append(score.field)
    by_field: dict[str, dict[str, FieldScore]] = {}
    for name in present:
        for score in comparison.scores[name]:
            by_field.setdefault(score.field, {})[name] = score
    for path in paths:
        golden_value = comparison.golden.get(path)
        cells = [path, _cell(golden_value, None)]
        for name in present:
            score = by_field.get(path, {}).get(name)
            cells.append(_cell(score.source if score else None, score.status if score else None))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def _cell(value: str | None, status: str | None) -> str:
    text = "—" if value is None else value.replace("|", "\\|").replace("\n", " ").replace("\r", " ")
    if status is None:
        return text
    return f"{_STATUS_MARK.get(status, '?')} {text}"


def render_markdown(comparisons: list[AlbumComparison]) -> str:
    """Render the full Markdown report: scorecard, enrichment quality, per-album field detail."""
    names = source_names(comparisons)
    out = ["# Parsing-quality report", ""]
    if HUFMAN not in names:
        out += ["> hufman column omitted (service unreachable or disabled).", ""]

    out += ["## Scorecard", "", "Field agreement against the golden (ground truth).", ""]
    out += ["| source | agreement | matches/scored |", "|---|---|---|"]
    for name, pct, ratio in _scorecard_rows(comparisons, names):
        out.append(f"| {name} | {pct} | {ratio} |")
    out.append("")

    backends = backend_names(comparisons)
    out += [
        "## Enrichment quality",
        "",
        "Per-track credits vs the enrichment golden (precision / recall / F1).",
        "",
    ]
    if not backends:
        out += ["No enrichment backends configured.", ""]
    else:
        out += [
            "| backend | precision | recall | F1 | matched/golden | produced |",
            "|---|---|---|---|---|---|",
        ]
        for backend in backends:
            agg = _aggregate_enrichment(comparisons, backend)
            out.append(
                f"| {backend} | {agg.precision:.2f} | {agg.recall:.2f} | {agg.f1:.2f} "
                f"| {agg.matched}/{agg.golden} | {agg.produced} |"
            )
        out += ["", "Per-album (recall / precision):", "", "| album | " + " | ".join(backends) + " |"]
        out.append("|" + "---|" * (1 + len(backends)))
        for comparison in comparisons:
            cells = [str(comparison.album_id)]
            for backend in backends:
                entry = comparison.enrichment.get(backend)
                cells.append(f"R {entry.score.recall:.2f} / P {entry.score.precision:.2f}" if entry else "—")
            out.append("| " + " | ".join(cells) + " |")
        out.append("")

    out += ["## Per-album field detail", ""]
    legend = "  ".join(f"`{mark}` {status}" for status, mark in _STATUS_MARK.items())
    out += [f"Status: {legend}", ""]
    for comparison in comparisons:
        out.append(f"### Album {comparison.album_id} — {comparison.title or ''}".rstrip(" —"))
        out.append("")
        out += _detail_table(comparison, names)
        out.append("")
    return "\n".join(out)

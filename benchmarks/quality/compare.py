"""Score canonical records against the golden and model the per-album comparison."""

from __future__ import annotations

from dataclasses import dataclass, field

from benchmarks.quality.adapters import CanonicalRecord
from benchmarks.quality.enrichment import EnrichmentScore
from benchmarks.quality.fields import normalize
from vgmdb_client.enrich import AlbumEnrichment
from vgmdb_client.models import Album

# Per-field scoring outcomes against the golden.
MATCH = "match"
MISMATCH = "mismatch"
MISSING = "missing"  # golden has a value, the source does not
EXTRA = "extra"  # the source has a value, the golden does not
ABSENT = "absent"  # neither has a value (not counted toward agreement)

# Source labels.
OURS = "ours"
HUFMAN = "hufman"


@dataclass(frozen=True)
class FieldScore:
    """A single field's value in both the source and the golden, plus the outcome."""

    field: str
    golden: str | None
    source: str | None
    status: str


@dataclass(frozen=True)
class Coverage:
    """ours+LLM enrichment coverage for one album (no golden ground truth exists)."""

    available: bool
    tracks_with_credits: int = 0
    total_tracks: int = 0
    total_credits: int = 0


@dataclass(frozen=True)
class EnrichmentEntry:
    """One named backend's enrichment result for an album: coverage + quality score vs the golden."""

    coverage: Coverage
    score: EnrichmentScore


@dataclass(frozen=True)
class AlbumComparison:
    """Everything needed to report one album: golden, each source's record, scores, enrichment."""

    album_id: int
    title: str | None
    golden: CanonicalRecord
    sources: dict[str, CanonicalRecord]
    scores: dict[str, list[FieldScore]]
    enrichment: dict[str, EnrichmentEntry] = field(default_factory=dict)


def score_record(source: CanonicalRecord, golden: CanonicalRecord) -> list[FieldScore]:
    """Score ``source`` against ``golden`` field by field (golden fields first, then source extras)."""
    paths = list(dict.fromkeys([*golden, *source]))
    scores: list[FieldScore] = []
    for path in paths:
        golden_value = golden.get(path)
        source_value = source.get(path)
        golden_norm = normalize(golden_value)
        source_norm = normalize(source_value)
        if golden_norm is None and source_norm is None:
            status = ABSENT
        elif golden_norm is not None and source_norm is not None:
            status = MATCH if golden_norm == source_norm else MISMATCH
        elif golden_norm is not None:
            status = MISSING
        else:
            status = EXTRA
        scores.append(FieldScore(path, golden_value, source_value, status))
    return scores


def agreement(scores: list[FieldScore]) -> tuple[int, int]:
    """Return ``(matches, scored)`` where scored counts only golden-present fields."""
    scored = [s for s in scores if s.status in (MATCH, MISMATCH, MISSING)]
    matches = [s for s in scored if s.status == MATCH]
    return len(matches), len(scored)


def coverage_for(album: Album, enrichment: AlbumEnrichment | None) -> Coverage:
    """Build enrichment coverage for an album; ``None`` enrichment means no backend was configured."""
    if enrichment is None:
        return Coverage(available=False)
    # track_credits is keyed by track number; reconcile against the album's real track numbers so the
    # coverage fraction stays coherent (and credits keyed to a non-existent track don't inflate it).
    valid_numbers = {track.number for disc in album.discs for track in disc.tracks if track.number is not None}
    credited = {number: entries for number, entries in enrichment.track_credits.items() if entries}
    in_album = {number: entries for number, entries in credited.items() if number in valid_numbers}
    return Coverage(
        available=True,
        tracks_with_credits=len(in_album),
        total_tracks=len(valid_numbers),
        total_credits=sum(len(entries) for entries in in_album.values()),
    )

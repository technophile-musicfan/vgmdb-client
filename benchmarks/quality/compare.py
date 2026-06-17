"""Score canonical records against the golden and model the per-album comparison."""

from __future__ import annotations

from dataclasses import dataclass, field

from benchmarks.quality.adapters import CanonicalRecord
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
class AlbumComparison:
    """Everything needed to report one album: golden, each source's record, scores, coverage."""

    album_id: int
    title: str | None
    golden: CanonicalRecord
    sources: dict[str, CanonicalRecord]
    scores: dict[str, list[FieldScore]]
    coverage: Coverage = field(default_factory=lambda: Coverage(available=False))


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
    total_tracks = sum(len(disc.tracks) for disc in album.discs)
    tracks_with_credits = sum(1 for entries in enrichment.track_credits.values() if entries)
    total_credits = sum(len(entries) for entries in enrichment.track_credits.values())
    return Coverage(
        available=True,
        tracks_with_credits=tracks_with_credits,
        total_tracks=total_tracks,
        total_credits=total_credits,
    )

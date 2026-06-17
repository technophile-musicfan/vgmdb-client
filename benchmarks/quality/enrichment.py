"""Score an AlbumEnrichment against an enrichment golden: precision / recall / F1 over credits."""

from __future__ import annotations

from dataclasses import dataclass

from vgmdb_client.enrich import AlbumEnrichment
from vgmdb_client.models import Credit


@dataclass(frozen=True)
class EnrichmentScore:
    """Per-track-credit quality of a produced enrichment against a golden."""

    matched: int
    produced: int
    golden: int

    @property
    def precision(self) -> float:
        # No produced credits => nothing wrong was emitted => precision 1.0.
        return self.matched / self.produced if self.produced else 1.0

    @property
    def recall(self) -> float:
        # Empty golden => nothing to find => recall 1.0.
        return self.matched / self.golden if self.golden else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def _artist_names(credit: Credit) -> frozenset[str]:
    """Casefolded artist names of a credit (default-language form)."""
    names = {(artist.names.default or "").casefold() for artist in credit.artists}
    return frozenset(name for name in names if name)


def _credits_match(a: Credit, b: Credit) -> bool:
    """Two credits match on same track-role and overlapping artist names (casefolded)."""
    if a.role != b.role:
        return False
    names_a, names_b = _artist_names(a), _artist_names(b)
    if not names_a and not names_b:
        return True  # both credit-only, no named artists
    return bool(names_a & names_b)


def score_enrichment(produced: AlbumEnrichment, golden: AlbumEnrichment) -> EnrichmentScore:
    """Match produced credits against golden credits per track number and tally precision/recall.

    Each golden credit may be matched by at most one produced credit (greedy, per track), so
    duplicating a credit does not inflate recall and unmatched produced credits cost precision.
    """
    matched = 0
    produced_total = 0
    golden_total = 0
    track_numbers = set(produced.track_credits) | set(golden.track_credits)
    for track in track_numbers:
        produced_credits = list(produced.track_credits.get(track, []))
        golden_credits = list(golden.track_credits.get(track, []))
        produced_total += len(produced_credits)
        golden_total += len(golden_credits)
        remaining = list(produced_credits)
        for golden_credit in golden_credits:
            hit = next((p for p in remaining if _credits_match(p, golden_credit)), None)
            if hit is not None:
                matched += 1
                remaining.remove(hit)
    return EnrichmentScore(matched=matched, produced=produced_total, golden=golden_total)

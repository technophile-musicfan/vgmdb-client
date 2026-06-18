"""Event entity model for vgmdb-client."""

from __future__ import annotations

from vgmdb_client.models.common import LocalizedText, PartialDate, VgmdbModel


class Event(VgmdbModel):
    """A vgmdb event (concert, convention, ...), core subset of fields.

    ``type`` is stored verbatim when the page shows one. ``end_date`` is ``None`` for a single-day
    event or when no distinct end is shown. Released-album / related lists are out of scope this pass.
    """

    id: int
    link: str | None = None
    names: LocalizedText
    type: str | None = None
    start_date: PartialDate | None = None
    end_date: PartialDate | None = None
    notes: str | None = None

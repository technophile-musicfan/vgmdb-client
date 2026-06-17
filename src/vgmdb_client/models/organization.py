"""Organization entity model for vgmdb-client."""

from __future__ import annotations

from vgmdb_client.models.common import LocalizedText, VgmdbModel


class Organization(VgmdbModel):
    """A vgmdb organization (company, doujin circle, label, ...), core subset of fields.

    ``type`` is stored verbatim (e.g. "Company", "Doujin Circle", "Label"). Released-album lists are
    out of scope this pass.
    """

    id: int
    link: str | None = None
    names: LocalizedText
    type: str | None = None
    notes: str | None = None

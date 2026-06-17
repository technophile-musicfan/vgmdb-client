"""Artist entity model for vgmdb-client."""

from __future__ import annotations

from pydantic import Field

from vgmdb_client.models.common import ArtistRef, LocalizedText, PartialDate, VgmdbModel


class Artist(VgmdbModel):
    """A vgmdb artist (person or unit), core subset of fields.

    ``type`` is stored verbatim as vgmdb shows it (e.g. "Person", "Unit"). ``members`` lists a unit's
    members; ``units`` lists the groups a person belongs to. Discography is out of scope this pass.
    """

    id: int
    link: str | None = None
    names: LocalizedText
    aliases: list[str] = Field(default_factory=list)
    type: str | None = None
    birthdate: PartialDate | None = None
    notes: str | None = None
    members: list[ArtistRef] = Field(default_factory=list)
    units: list[ArtistRef] = Field(default_factory=list)

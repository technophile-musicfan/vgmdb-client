"""Album entity models for vgmdb-client."""

from __future__ import annotations

from pydantic import Field

from vgmdb_client.models.common import ArtistRef, LocalizedText, PartialDate, VgmdbModel
from vgmdb_client.models.roles import Role


class Track(VgmdbModel):
    """A single track on a disc."""

    titles: LocalizedText
    number: int | None = None
    length: str | None = None


class Disc(VgmdbModel):
    """A disc within an album, holding its tracks."""

    number: int | None = None
    name: str | None = None
    tracks: list[Track] = Field(default_factory=list)


class Credit(VgmdbModel):
    """An album credit: a normalized role, the verbatim source label, and its artists."""

    role: Role
    role_raw: str
    artists: list[ArtistRef] = Field(default_factory=list)


class Album(VgmdbModel):
    """A vgmdb album (core subset of fields)."""

    id: int
    link: str | None = None
    titles: LocalizedText
    catalog: str | None = None
    release_date: PartialDate | None = None
    classification: str | None = None
    cover_small: str | None = None
    cover_full: str | None = None
    discs: list[Disc] = Field(default_factory=list)
    credits: list[Credit] = Field(default_factory=list)
    notes: str | None = None

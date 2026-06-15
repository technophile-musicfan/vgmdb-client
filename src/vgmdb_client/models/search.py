"""Search result models for vgmdb-client (albums only)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from vgmdb_client.models.common import LocalizedText, PartialDate


class AlbumSearchResult(BaseModel):
    """A single album entry in search results."""

    id: int
    link: str | None = None
    titles: LocalizedText
    catalog: str | None = None
    release_date: PartialDate | None = None


class SearchResults(BaseModel):
    """Results of an album search."""

    query: str
    albums: list[AlbumSearchResult] = Field(default_factory=list)

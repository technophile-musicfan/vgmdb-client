"""Product entity model for vgmdb-client."""

from __future__ import annotations

from pydantic import Field

from vgmdb_client.models.common import LocalizedText, OrgRef, ProductRef, VgmdbModel


class Product(VgmdbModel):
    """A vgmdb product (game, franchise, animation, ...), core subset of fields.

    ``type`` is stored verbatim (e.g. "Game", "Franchise"). ``franchises`` lists parent/related
    products; ``organizations`` lists developers/publishers. Related-album lists are out of scope.
    """

    id: int
    link: str | None = None
    names: LocalizedText
    type: str | None = None
    notes: str | None = None
    franchises: list[ProductRef] = Field(default_factory=list)
    organizations: list[OrgRef] = Field(default_factory=list)

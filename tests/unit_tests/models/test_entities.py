"""Tests for the B3 entity models (Artist, Product, Organization) and the new refs."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from vgmdb_client.models import (
    Artist,
    ArtistRef,
    LocalizedText,
    Organization,
    OrgRef,
    PartialDate,
    Product,
    ProductRef,
)


def _names(text: str) -> LocalizedText:
    return LocalizedText({"English": text})


# --- lightweight refs ---------------------------------------------------------------------


def test_product_ref_carries_fields() -> None:
    ref = ProductRef(names=_names("Xenogears"), id=108, link="https://vgmdb.net/product/108")
    assert ref.names.default == "Xenogears"
    assert ref.id == 108
    assert ref.link == "https://vgmdb.net/product/108"


def test_org_ref_defaults_id_and_link() -> None:
    ref = OrgRef(names=_names("Square"))
    assert ref.id is None
    assert ref.link is None


# --- Artist -------------------------------------------------------------------------------


def test_artist_carries_identity_metadata_and_members() -> None:
    artist = Artist(
        id=73,
        names=_names("Yasunori Mitsuda"),
        type="Person",
        birthdate=PartialDate(year=1972, month=1, day=21),
        members=[ArtistRef(names=_names("Someone"), id=1)],
    )
    assert artist.names.default == "Yasunori Mitsuda"
    assert artist.type == "Person"
    assert artist.birthdate is not None and str(artist.birthdate) == "1972-01-21"
    assert artist.members[0].id == 1
    assert artist.aliases == []  # defaults
    assert artist.units == []


def test_artist_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        Artist(id=1, names=_names("X"), bogus="nope")  # type: ignore[call-arg]


def test_artist_is_frozen() -> None:
    artist = Artist(id=1, names=_names("X"))
    with pytest.raises(ValidationError):
        artist.type = "Unit"  # type: ignore[misc]


# --- Product ------------------------------------------------------------------------------


def test_product_carries_metadata_and_cross_refs() -> None:
    product = Product(
        id=108,
        names=_names("Xenogears"),
        type="Game",
        franchises=[ProductRef(names=_names("Xeno"), id=1)],
        organizations=[OrgRef(names=_names("Square"), id=29)],
    )
    assert product.type == "Game"
    assert product.franchises[0].id == 1
    assert product.organizations[0].id == 29
    assert product.notes is None


def test_product_lists_default_empty() -> None:
    product = Product(id=1, names=_names("X"))
    assert product.franchises == []
    assert product.organizations == []


# --- Organization -------------------------------------------------------------------------


def test_organization_carries_identity_and_verbatim_type() -> None:
    org = Organization(id=29, names=_names("Square"), type="Company")
    assert org.names.default == "Square"
    assert org.type == "Company"
    assert org.notes is None


def test_organization_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        Organization(id=1, names=_names("X"), albums=[])  # type: ignore[call-arg]

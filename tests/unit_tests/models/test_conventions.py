"""Tests for cross-model conventions (frozen, extra-forbid) and public exports."""

import pytest
from pydantic import ValidationError

import vgmdb_client.models as models
from vgmdb_client.models import (
    Album,
    AlbumSearchResult,
    ArtistRef,
    Credit,
    Disc,
    LocalizedText,
    PartialDate,
    SearchResults,
    Track,
)


def _titles(**langs: str) -> LocalizedText:
    return LocalizedText(langs)


def test_models_are_frozen() -> None:
    album = Album(id=1, titles=_titles(English="X"))
    with pytest.raises(ValidationError):
        album.id = 2  # type: ignore[misc]


def test_value_types_are_frozen() -> None:
    date = PartialDate(year=2007)
    with pytest.raises(ValidationError):
        date.year = 2008  # type: ignore[misc]


def test_unknown_field_rejected() -> None:
    with pytest.raises(ValidationError):
        Album(id=1, titles=_titles(English="X"), bogus="nope")  # type: ignore[call-arg]


def test_unknown_field_rejected_on_search_result() -> None:
    with pytest.raises(ValidationError):
        AlbumSearchResult(id=1, titles=_titles(English="X"), bogus="nope")  # type: ignore[call-arg]


def test_public_surface_exported() -> None:
    expected = {
        "LocalizedText",
        "PartialDate",
        "ArtistRef",
        "Track",
        "Disc",
        "Credit",
        "Album",
        "AlbumSearchResult",
        "SearchResults",
    }
    assert expected <= set(models.__all__)
    for name in expected:
        assert getattr(models, name) is not None


def test_role_and_normalize_role_are_exported() -> None:
    from vgmdb_client.models import Role, normalize_role

    assert Role.COMPOSER == "composer"
    assert normalize_role("Composer") is Role.COMPOSER


def test_exported_symbols_are_the_model_classes() -> None:
    assert Credit is models.Credit
    assert Disc is models.Disc
    assert Track is models.Track
    assert ArtistRef is models.ArtistRef
    assert SearchResults is models.SearchResults

"""Tests for album entity models (Track, Disc, Credit, Album)."""

import pytest
from pydantic import ValidationError

from vgmdb_client.models.album import Album, Credit, Disc, Track
from vgmdb_client.models.common import ArtistRef, LocalizedText, PartialDate
from vgmdb_client.models.roles import Role


def _titles(**langs: str) -> LocalizedText:
    return LocalizedText(langs)


def test_track_construction_and_defaults() -> None:
    track = Track(titles=_titles(English="Song of the Ancients"), number=3, length="4:35")
    assert track.titles.prefer("English") == "Song of the Ancients"
    assert track.number == 3
    assert track.length == "4:35"

    bare = Track(titles=_titles(English="Untitled"))
    assert bare.number is None
    assert bare.length is None


def test_disc_holds_tracks_with_defaults() -> None:
    disc = Disc(number=1, name="Disc 1", tracks=[Track(titles=_titles(English="A"))])
    assert disc.number == 1
    assert disc.name == "Disc 1"
    assert len(disc.tracks) == 1

    bare = Disc()
    assert bare.number is None
    assert bare.name is None
    assert bare.tracks == []


def test_credit_carries_normalized_role_and_raw_label() -> None:
    credit = Credit(
        role=Role.ARRANGER,
        role_raw="Arrangement",
        artists=[ArtistRef(names=_titles(English="Keiichi Okabe"), id=770)],
    )
    assert credit.role is Role.ARRANGER
    assert credit.role_raw == "Arrangement"
    assert credit.artists[0].id == 770

    assert Credit(role=Role.COMPOSER, role_raw="Composer").artists == []


def test_credit_requires_role_raw() -> None:
    with pytest.raises(ValidationError):
        Credit(role=Role.COMPOSER)  # type: ignore[call-arg]


def test_credit_rejects_unknown_role_value() -> None:
    with pytest.raises(ValidationError):
        Credit(role="not-a-real-role", role_raw="Whatever")  # type: ignore[arg-type]


def test_album_full_construction() -> None:
    album = Album(
        id=123,
        link="album/123",
        titles=_titles(English="NieR Gestalt & Replicant OST"),
        catalog="SQEX-10165~7",
        release_date=PartialDate(year=2010, month=4, day=21),
        classification="Original Soundtrack",
        cover_small="https://medium-media.vgm.io/albums/x/123/s.jpg",
        cover_full="https://media.vgm.io/albums/x/123/f.jpg",
        discs=[Disc(number=1, tracks=[Track(titles=_titles(English="Snow in Summer"))])],
        credits=[
            Credit(
                role=Role.COMPOSER,
                role_raw="Composer",
                artists=[ArtistRef(names=_titles(English="Keiichi Okabe"))],
            )
        ],
        notes="freeform notes",
    )
    assert album.id == 123
    assert album.release_date is not None
    assert str(album.release_date) == "2010-04-21"
    assert album.discs[0].tracks[0].titles.prefer("English") == "Snow in Summer"
    assert album.credits[0].role is Role.COMPOSER
    assert album.credits[0].role_raw == "Composer"


def test_album_partial_construction_defaults() -> None:
    album = Album(id=1, titles=_titles(English="Minimal"))
    assert album.link is None
    assert album.catalog is None
    assert album.release_date is None
    assert album.classification is None
    assert album.cover_small is None
    assert album.cover_full is None
    assert album.discs == []
    assert album.credits == []
    assert album.notes is None

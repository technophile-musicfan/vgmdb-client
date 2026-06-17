"""The enrichment golden dataset is well-formed and covers every album fixture."""

from __future__ import annotations

import pytest

from tests.support.fixtures import (
    iter_album_fixtures,
    iter_enrichment_goldens,
    load_album_fixture,
    load_enrichment_golden,
)
from vgmdb_client.enrich import AlbumEnrichment


def test_every_album_fixture_has_an_enrichment_golden() -> None:
    assert set(iter_enrichment_goldens()) == set(iter_album_fixtures())


@pytest.mark.parametrize("album_id", sorted(iter_enrichment_goldens()))
def test_enrichment_golden_loads_and_validates(album_id: int) -> None:
    golden = load_enrichment_golden(album_id)
    assert isinstance(golden, AlbumEnrichment)
    assert golden.album_id == album_id


@pytest.mark.parametrize("album_id", sorted(iter_enrichment_goldens()))
def test_enrichment_golden_track_numbers_exist_on_the_album(album_id: int) -> None:
    # A golden must only credit tracks the album actually has.
    _, album = load_album_fixture(album_id)
    track_numbers = {t.number for disc in album.discs for t in disc.tracks if t.number is not None}
    credited = set(load_enrichment_golden(album_id).track_credits)
    assert credited <= track_numbers

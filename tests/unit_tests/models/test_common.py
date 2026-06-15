"""Tests for shared value types (LocalizedText, PartialDate, ArtistRef)."""

import pytest
from pydantic import ValidationError

from vgmdb_client.models.common import ArtistRef, LocalizedText, PartialDate


def _localized(**langs: str) -> LocalizedText:
    return LocalizedText(langs)


# --- LocalizedText --------------------------------------------------------


def test_prefer_returns_requested_language_when_present() -> None:
    text = _localized(English="Nier", Japanese="ニーア")
    assert text.prefer("Japanese") == "ニーア"


def test_prefer_falls_back_to_default_when_absent() -> None:
    text = _localized(English="Nier", Japanese="ニーア")
    assert text.prefer("German") == "Nier"


def test_default_prefers_english() -> None:
    text = _localized(Japanese="ニーア", Romaji="Nia", English="Nier")
    assert text.default == "Nier"


def test_default_uses_romaji_when_no_english() -> None:
    text = _localized(Japanese="ニーア", Romaji="Nia")
    assert text.default == "Nia"


def test_default_falls_back_to_any_when_no_english_or_romaji() -> None:
    text = _localized(Japanese="ニーア")
    assert text.default == "ニーア"


def test_empty_default_is_none() -> None:
    assert LocalizedText({}).default is None


def test_all_returns_mapping() -> None:
    text = _localized(English="Nier")
    assert text.all == {"English": "Nier"}


def test_str_is_default_or_empty() -> None:
    assert str(_localized(English="Nier")) == "Nier"
    assert str(LocalizedText({})) == ""


# --- PartialDate ----------------------------------------------------------


def test_year_only_precision_and_str() -> None:
    date = PartialDate(year=2007)
    assert date.precision == "year"
    assert str(date) == "2007"


def test_year_month_precision_and_str() -> None:
    date = PartialDate(year=2007, month=8)
    assert date.precision == "month"
    assert str(date) == "2007-08"


def test_full_date_precision_and_str() -> None:
    date = PartialDate(year=2007, month=8, day=1)
    assert date.precision == "day"
    assert str(date) == "2007-08-01"


def test_day_without_month_rejected() -> None:
    with pytest.raises(ValidationError):
        PartialDate(year=2007, day=1)


def test_out_of_range_month_rejected() -> None:
    with pytest.raises(ValidationError):
        PartialDate(year=2007, month=13)


def test_out_of_range_day_rejected() -> None:
    with pytest.raises(ValidationError):
        PartialDate(year=2007, month=8, day=32)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2007", PartialDate(year=2007)),
        ("2007-08", PartialDate(year=2007, month=8)),
        ("2007-08-01", PartialDate(year=2007, month=8, day=1)),
    ],
)
def test_parse_valid_shapes(value: str, expected: PartialDate) -> None:
    assert PartialDate.parse(value) == expected


@pytest.mark.parametrize("value", ["", "not-a-date", "2007/08/01", "2007-13"])
def test_parse_unparseable_returns_none(value: str) -> None:
    assert PartialDate.parse(value) is None


# --- ArtistRef ------------------------------------------------------------


def test_artist_ref_with_id_and_link() -> None:
    ref = ArtistRef(names=_localized(English="Keiichi Okabe"), id=770, link="artist/770")
    assert ref.names.prefer("English") == "Keiichi Okabe"
    assert ref.id == 770
    assert ref.link == "artist/770"


def test_artist_ref_optionals_default_to_none() -> None:
    ref = ArtistRef(names=_localized(English="Unknown"))
    assert ref.id is None
    assert ref.link is None

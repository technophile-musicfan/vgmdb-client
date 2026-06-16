"""Tests for the normalized credit-role vocabulary and mapping."""

import pytest

from vgmdb_client.models.roles import Role, normalize_role


def test_role_is_str_enum_with_expected_members() -> None:
    assert Role.COMPOSER == "composer"
    assert Role.OTHER == "other"
    names = {r.name for r in Role}
    assert names == {
        "COMPOSER",
        "ARRANGER",
        "PERFORMER",
        "VOCALIST",
        "LYRICIST",
        "PRODUCER",
        "ENGINEER",
        "MIXING",
        "MASTERING",
        "DIRECTOR",
        "CONDUCTOR",
        "ARTWORK",
        "OTHER",
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Composer", Role.COMPOSER),
        ("Original Music Composed by", Role.COMPOSER),
        ("Arranger", Role.ARRANGER),
        ("Arrangement", Role.ARRANGER),
        ("Lyrics", Role.LYRICIST),
        ("Words", Role.LYRICIST),
        ("Written by", Role.LYRICIST),
        ("Vocals", Role.VOCALIST),
        ("Producer", Role.PRODUCER),
        ("Executive Producer", Role.PRODUCER),
        ("Mastering Studio", Role.MASTERING),
        ("Mastered by", Role.MASTERING),
        ("Mixing Engineer", Role.MIXING),
        ("Recording Engineer", Role.ENGINEER),
        ("Recording Studio", Role.ENGINEER),
        ("Conductor", Role.CONDUCTOR),
        ("Directed by", Role.DIRECTOR),
        ("Jacket Illustration", Role.ARTWORK),
        ("Acoustic Guitar", Role.PERFORMER),
        ("1st Violin", Role.PERFORMER),
        ("Performed by", Role.PERFORMER),
    ],
)
def test_normalize_role_maps_known_labels(raw: str, expected: Role) -> None:
    assert normalize_role(raw) == expected


def test_normalize_role_is_case_insensitive() -> None:
    assert normalize_role("ARRANGEMENT") == Role.ARRANGER
    assert normalize_role("arrangement") == Role.ARRANGER


def test_normalize_role_unknown_maps_to_other() -> None:
    assert normalize_role("Special Thanks") == Role.OTHER
    assert normalize_role("Sales Promotion") == Role.OTHER
    assert normalize_role("") == Role.OTHER


def test_mastering_and_mixing_precede_generic_engineer() -> None:
    assert normalize_role("Mastering Engineer") == Role.MASTERING
    assert normalize_role("Mixing Engineer") == Role.MIXING

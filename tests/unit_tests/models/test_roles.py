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
        ("Art Direction", Role.ARTWORK),
        ("Recording Producer", Role.PRODUCER),
        ("Acoustic Guitar", Role.PERFORMER),
        ("1st Violin", Role.PERFORMER),
        ("Performed by", Role.PERFORMER),
        ("Music", Role.COMPOSER),  # bare "Music" credit is a composer
        ("Assistant Engineer", Role.ENGINEER),  # "assistant" alone must not become OTHER
    ],
)
def test_normalize_role_maps_known_labels(raw: str, expected: Role) -> None:
    assert normalize_role(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "Production Coordinator",
        "Production Manager",
        "Production Assistant",
        "Recording Coordinator",
        "Music Licensing Manager",
    ],
)
def test_normalize_role_administrative_roles_map_to_other(raw: str) -> None:
    # Coordination/management roles are OTHER even when they contain a producer/
    # recording substring (the verbatim label is preserved on Credit.role_raw).
    assert normalize_role(raw) == Role.OTHER


@pytest.mark.parametrize(
    "raw",
    [
        "Record Label",  # not a recording-engineer credit ("record" must not over-match)
        "Concertmaster",  # contains "master" but is a performer role, not mastering
        "Remix",  # contains "mix" but is not a mixing credit
        "Special Thanks",
    ],
)
def test_normalize_role_conservative_unknowns_map_to_other(raw: str) -> None:
    assert normalize_role(raw) == Role.OTHER


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

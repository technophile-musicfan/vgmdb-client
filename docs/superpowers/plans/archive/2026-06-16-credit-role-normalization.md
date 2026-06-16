# Credit Role Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `Credit` a normalized `role` (controlled `Role` vocabulary) plus the verbatim `role_raw`, with a shared `normalize_role` mapping in the models layer.

**Architecture:** New pure module `src/vgmdb_client/models/roles.py` holds a `Role` enum and a conservative, case-insensitive `normalize_role(raw) -> Role`. `Credit` (in `album.py`) changes `role: str` → `role: Role` and gains required `role_raw: str`. Public surface re-exported from `models/__init__.py`. M3's parser will call `normalize_role`; this change adds no parser.

**Tech Stack:** Python ≥3.10 (so `class Role(str, Enum)`, NOT `enum.StrEnum` which is 3.11+), pydantic v2, pytest, ruff, mypy, uv.

---

## File Structure

- **Create** `src/vgmdb_client/models/roles.py` — `Role` enum + `normalize_role` + mapping table.
- **Create** `tests/unit_tests/models/test_roles.py` — unit tests for the enum + mapping.
- **Modify** `src/vgmdb_client/models/album.py` — `Credit` shape change (add `from vgmdb_client.models.roles import Role`).
- **Modify** `src/vgmdb_client/models/__init__.py` — re-export `Role`, `normalize_role`.
- **Modify** `tests/unit_tests/models/test_album.py` (or `test_conventions.py`) — `Credit` tests for new shape.

All commands run from the worktree root `C:/Users/ml-na/PycharmProjects/personal/vgmdb-client/.claude/worktrees/credit-role-normalization`. Use `uv run` for pytest/ruff/mypy.

---

### Task 1: `Role` enum + `normalize_role` (roles.py)

**Files:**
- Create: `src/vgmdb_client/models/roles.py`
- Test: `tests/unit_tests/models/test_roles.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit_tests/models/test_roles.py
"""Tests for the normalized credit-role vocabulary and mapping."""

import pytest

from vgmdb_client.models.roles import Role, normalize_role


def test_role_is_str_enum_with_expected_members() -> None:
    assert Role.COMPOSER == "composer"
    assert Role.OTHER == "other"
    names = {r.name for r in Role}
    assert names == {
        "COMPOSER", "ARRANGER", "PERFORMER", "VOCALIST", "LYRICIST",
        "PRODUCER", "ENGINEER", "MIXING", "MASTERING", "DIRECTOR",
        "CONDUCTOR", "ARTWORK", "OTHER",
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
    # "...Engineer" labels must resolve to the more specific role first
    assert normalize_role("Mastering Engineer") == Role.MASTERING
    assert normalize_role("Mixing Engineer") == Role.MIXING
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit_tests/models/test_roles.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'vgmdb_client.models.roles'`

- [ ] **Step 3: Write the implementation**

```python
# src/vgmdb_client/models/roles.py
"""Normalized credit-role vocabulary and the mapping from freeform vgmdb labels.

vgmdb credit labels are freeform (e.g. "Original Music Composed by", "Mastering Studio").
``normalize_role`` maps them to a small controlled vocabulary; the verbatim label is kept
separately on ``Credit.role_raw``. Mapping is conservative: anything not confidently matched
becomes ``Role.OTHER``.
"""

from __future__ import annotations

from enum import Enum

# NOTE: Python >=3.10 target, so `class Role(str, Enum)` rather than enum.StrEnum (3.11+).


class Role(str, Enum):
    """Normalized credit role. ``OTHER`` is the conservative fallback."""

    COMPOSER = "composer"
    ARRANGER = "arranger"
    PERFORMER = "performer"
    VOCALIST = "vocalist"
    LYRICIST = "lyricist"
    PRODUCER = "producer"
    ENGINEER = "engineer"
    MIXING = "mixing"
    MASTERING = "mastering"
    DIRECTOR = "director"
    CONDUCTOR = "conductor"
    ARTWORK = "artwork"
    OTHER = "other"


# Ordered (keyword, role) rules; FIRST substring match wins on the casefolded label.
# Order matters: more specific before generic (mastering/mixing before engineer;
# lyric/words before performer; orchestrat before generic).
_RULES: tuple[tuple[str, Role], ...] = (
    ("compos", Role.COMPOSER),
    ("orchestrat", Role.ARRANGER),
    ("arrang", Role.ARRANGER),
    ("lyric", Role.LYRICIST),
    ("words", Role.LYRICIST),
    ("written by", Role.LYRICIST),
    ("master", Role.MASTERING),
    ("mix", Role.MIXING),
    ("record", Role.ENGINEER),
    ("engineer", Role.ENGINEER),
    ("pro tools", Role.ENGINEER),
    ("produc", Role.PRODUCER),
    ("conduct", Role.CONDUCTOR),
    ("direct", Role.DIRECTOR),
    ("illustrat", Role.ARTWORK),
    ("jacket", Role.ARTWORK),
    ("art direction", Role.ARTWORK),
    ("artwork", Role.ARTWORK),
    ("vocal", Role.VOCALIST),
    ("chorus", Role.VOCALIST),
    # instruments -> performer (specific instrument kept in role_raw)
    ("guitar", Role.PERFORMER),
    ("bass", Role.PERFORMER),
    ("violin", Role.PERFORMER),
    ("viola", Role.PERFORMER),
    ("cello", Role.PERFORMER),
    ("piano", Role.PERFORMER),
    ("keyboard", Role.PERFORMER),
    ("drum", Role.PERFORMER),
    ("percussion", Role.PERFORMER),
    ("flute", Role.PERFORMER),
    ("shakuhachi", Role.PERFORMER),
    ("shinobue", Role.PERFORMER),
    ("bouzouki", Role.PERFORMER),
    ("synthesizer", Role.PERFORMER),
    ("perform", Role.PERFORMER),
)


def normalize_role(raw: str) -> Role:
    """Map a freeform vgmdb role label to a :class:`Role` (conservative; unknown -> OTHER)."""
    label = raw.casefold()
    for keyword, role in _RULES:
        if keyword in label:
            return role
    return Role.OTHER
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit_tests/models/test_roles.py -q`
Expected: PASS (all parametrized cases green). If any case fails, adjust `_RULES` ordering/keywords — do NOT change the test expectations.

- [ ] **Step 5: Commit**

```bash
git add src/vgmdb_client/models/roles.py tests/unit_tests/models/test_roles.py
git commit -m "feat(models): add Role vocabulary and normalize_role mapping"
```

---

### Task 2: `Credit` model change + exports

**Files:**
- Modify: `src/vgmdb_client/models/album.py` (the `Credit` class)
- Modify: `src/vgmdb_client/models/__init__.py`
- Test: `tests/unit_tests/models/test_album.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/unit_tests/models/test_album.py` (imports at top: `from vgmdb_client.models import Credit, ArtistRef, LocalizedText, Role`):

```python
def test_credit_carries_normalized_role_and_raw_label() -> None:
    c = Credit(
        role=Role.ARRANGER,
        role_raw="Arrangement",
        artists=[ArtistRef(names=LocalizedText({"English": "X"}))],
    )
    assert c.role is Role.ARRANGER
    assert c.role_raw == "Arrangement"
    assert len(c.artists) == 1


def test_credit_requires_role_raw() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Credit(role=Role.COMPOSER)  # type: ignore[call-arg]  # missing role_raw


def test_credit_rejects_unknown_role_value() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Credit(role="not-a-real-role", role_raw="Whatever")  # type: ignore[arg-type]
```

And add an import smoke test in `tests/unit_tests/models/test_conventions.py` (extend the existing imports / add):

```python
def test_role_and_normalize_role_are_exported() -> None:
    from vgmdb_client.models import Role, normalize_role

    assert Role.COMPOSER == "composer"
    assert normalize_role("Composer") is Role.COMPOSER
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit_tests/models/test_album.py -q -k credit`
Expected: FAIL (`Credit` has no `role_raw`; `role` accepts arbitrary str).

- [ ] **Step 3: Change `Credit` and exports**

In `src/vgmdb_client/models/album.py`, add the import near the top:

```python
from vgmdb_client.models.roles import Role
```

Replace the `Credit` class body:

```python
class Credit(VgmdbModel):
    """An album credit: a normalized role, the verbatim source label, and its artists."""

    role: Role
    role_raw: str
    artists: list[ArtistRef] = Field(default_factory=list)
```

In `src/vgmdb_client/models/__init__.py`, add to the imports and `__all__`:

```python
from vgmdb_client.models.roles import Role, normalize_role
```
Add `"Role"` and `"normalize_role"` to the `__all__` list (keep it alphabetically sorted to match existing style).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit_tests/models/ -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/vgmdb_client/models/album.py src/vgmdb_client/models/__init__.py tests/unit_tests/models/test_album.py tests/unit_tests/models/test_conventions.py
git commit -m "feat(models): Credit carries normalized role + verbatim role_raw"
```

---

### Task 3: Conventions & full green

**Files:** none (verification)

- [ ] **Step 1: Run ruff**

Run: `uv run ruff check src/ tests/ && uv run ruff format --check src/vgmdb_client/models/roles.py tests/unit_tests/models/test_roles.py`
Expected: "All checks passed!"; format clean for the new files (run `uv run ruff format <those files>` if needed and re-commit).

- [ ] **Step 2: Run mypy**

Run: `uv run mypy`
Expected: "Success: no issues found".

- [ ] **Step 3: Run the full test suite**

Run: `uv run pytest -q`
Expected: all pass.

- [ ] **Step 4: Commit any fixups**

```bash
git add -A && git commit -m "chore(models): lint/type fixups for role normalization"
```
(Skip if nothing changed.)

---

## Notes for the implementer

- The `_RULES` table is the conservative starting point. If a real label maps wrong, adjust the keyword/order — but keep the rule conservative (prefer `OTHER` over a confident-but-wrong category). Do not weaken the spec's scenarios.
- Bare ambiguous labels (e.g. "Music", "Sound Design") intentionally fall through to `OTHER` — the raw label is preserved on `role_raw`.
- Do NOT use `enum.StrEnum` (Python 3.11+); the project targets ≥3.10.

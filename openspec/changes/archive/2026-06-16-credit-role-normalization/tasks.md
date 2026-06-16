## 1. Role vocabulary & mapping (roles.py)

- [x] 1.1 Implement the `Role` `StrEnum` (`COMPOSER, ARRANGER, PERFORMER, VOCALIST, LYRICIST, PRODUCER, ENGINEER, MIXING, MASTERING, DIRECTOR, CONDUCTOR, ARTWORK, OTHER`, values like `"composer"`) in `src/vgmdb_client/models/roles.py`; test members and string values
- [x] 1.2 Implement `normalize_role(raw: str) -> Role`: case-insensitive, conservative keyword/substring mapping table, ordered to avoid mis-maps (e.g. master/mix before generic engineer); unmatched → `OTHER`; test the labels M5 surfaced (Composer, "Original Music Composed by", Arranger/Arrangement, Lyrics/Words/"Written by", Vocals, Mastering Studio, "Recording Studio", instruments→PERFORMER, "Special Thanks"→OTHER) + case-insensitivity

## 2. Credit model change (album.py)

- [x] 2.1 Change `Credit` to `role: Role` (normalized) + `role_raw: str` (required, always set), `artists` unchanged; keep `frozen=True, extra="forbid"`; test normalized role + `role_raw` accessible, `role_raw` required, invalid enum and unknown keys rejected, immutability preserved
- [x] 2.2 Re-export `Role` and `normalize_role` from `models/__init__.py` (and package surface as appropriate); test imports

## 3. Conventions & wiring

- [x] 3.1 Run ruff, mypy, and the full test suite; fix until green

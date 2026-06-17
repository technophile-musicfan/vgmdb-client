## 1. Track-range parsing

- [ ] 1.1 `src/vgmdb_client/enrich/rules.py`: `_parse_track_set(text) -> set[int]` handling comma
  lists, `~` ranges, and `M`/`M-`/leading-zero prefixes (`1,4,5`, `1~3`, `01, 07`, `M-01`,
  `M01~12, 14~23`). Unit-test each notation.

## 2. RuleBasedBackend

- [ ] 2.1 `RuleBasedBackend.enrich(album, raw_text)`: line scanner with the inline-parenthetical
  pattern (`<Name> (<ranges>)` under a role context) and the block pattern (range/number header sets
  the current track set; following `<Role> by/: <Names>` lines attribute to it). `normalize_role` on
  role_raw; names split on `,`/`&`/`and`/`;`; credits keyed by track number into `AlbumEnrichment`.
- [ ] 2.2 Precision safeguard: emit credits only with a track context or inline ranges. Export
  `RuleBasedBackend` from `enrich/__init__.py`. Unit-test extractor on representative note snippets.

## 3. Golden-scored tests + gate

- [ ] 3.1 Via the Cycle 1 scorer: assert high recall on clean albums (10000, 22000) and precision 1.0
  on the empty-golden albums (4, 5012, 30000, 60000 — no hallucination).
- [ ] 3.2 Full gate (ruff + mypy + pytest) green.

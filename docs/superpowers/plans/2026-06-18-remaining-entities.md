# V1b Remaining Entities Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the vgmdb `Event` entity (model + clean-room parser + sync/async client) and link an album to its release event via an additive `Album.release_event`.

**Architecture:** Mirror the established entity pattern (frozen `VgmdbModel` + canonical-link-keyed clean-room parser + `get_*` client methods + captured HTML fixture & hand-authored golden). The Album change is purely additive (`release_event` defaults to `None`).

**Tech Stack:** Python 3.10+, pydantic v2, lxml, pytest, uv. Worktree: `C:\Users\ml-na\PycharmProjects\personal\vgmdb-client-entities` (branch `feat/remaining-entities`).

**Spec inputs:** `docs/superpowers/vgmdb_client/2026-06-18_remaining_entities_design.md`; `openspec/changes/remaining-entities/` (specs for models/parsers/client).

**Confirmed from the captured `tests/fixtures/vgmdb/events/149.html`:**
- Canonical link present: `https://vgmdb.net/event/149` (id source; `//link[@rel="canonical"]` is attribute-order-independent).
- No `<h1>`. The event's own name is the **leading group** of `albumtitle` spans (the page has 96 such spans — related albums — so scope to the first group via the `_leading_group` idiom, as the product parser does).
- Name resolves via `_dom.localized_text` to `{"English": "Hakurei Shrine Reitaisai 9", "Japanese": "博麗神社例大祭（第9回）"}` (Romaji == English, so dropped by `_placeholder_rule`).
- Date "May 27, 2012" → `_dom.partial_date` → `PartialDate(year=2012, month=5, day=27)`. Single-day event → `end_date = None`.
- Location ("International Exhibition Center") is out of the core-subset scope.

---

## File Structure

- Create `src/vgmdb_client/models/event.py` — `Event` model.
- Modify `src/vgmdb_client/models/common.py` — add `EventRef`.
- Modify `src/vgmdb_client/models/album.py` — add `release_event` field.
- Modify `src/vgmdb_client/models/__init__.py` and `src/vgmdb_client/__init__.py` — export `Event`, `EventRef`.
- Create `src/vgmdb_client/parsers/event.py` — `parse_event`.
- Modify `src/vgmdb_client/parsers/errors.py` — add `NotAnEventPageError`.
- Modify `src/vgmdb_client/parsers/__init__.py` — export `parse_event`, `NotAnEventPageError`.
- Modify `src/vgmdb_client/parsers/album.py` — populate `release_event`.
- Modify `src/vgmdb_client/client/_core.py` — `event_path`.
- Modify `src/vgmdb_client/client/sync_client.py` + `async_client.py` — `get_event`.
- Modify `tests/support/fixtures.py` — `load_event_fixture`.
- Create `tests/fixtures/vgmdb/events/149.json` — hand-authored golden (no parser).
- Modify `tests/fixtures/vgmdb/albums/33000.json` — add expected `release_event`.
- Tests: `tests/unit_tests/models/`, `tests/unit_tests/parsers/`, `tests/unit_tests/client/`.

---

## Task 1: EventRef + Event model

**Files:**
- Modify: `src/vgmdb_client/models/common.py`
- Create: `src/vgmdb_client/models/event.py`
- Modify: `src/vgmdb_client/models/__init__.py`, `src/vgmdb_client/__init__.py`
- Test: `tests/unit_tests/models/test_event.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit_tests/models/test_event.py
from __future__ import annotations
import pytest
from pydantic import ValidationError
from vgmdb_client import Event, EventRef
from vgmdb_client.models import LocalizedText, PartialDate

def test_event_full() -> None:
    e = Event(id=149, link="https://vgmdb.net/event/149",
              names=LocalizedText({"English": "Hakurei Shrine Reitaisai 9"}),
              start_date=PartialDate(year=2012, month=5, day=27))
    assert e.id == 149 and e.start_date.year == 2012 and e.end_date is None

def test_event_partial_defaults() -> None:
    e = Event(id=1, names=LocalizedText({"English": "X"}))
    assert e.link is None and e.type is None and e.start_date is None and e.notes is None

def test_event_is_frozen_and_rejects_unknown() -> None:
    e = Event(id=1, names=LocalizedText({"English": "X"}))
    with pytest.raises(ValidationError):
        e.id = 2  # type: ignore[misc]
    with pytest.raises(ValidationError):
        Event(id=1, names=LocalizedText({"English": "X"}), bogus=1)  # type: ignore[call-arg]

def test_event_ref() -> None:
    r = EventRef(names=LocalizedText({"English": "X"}), id=149)
    assert r.id == 149 and r.link is None
```

- [ ] **Step 2: Run, verify import failure**

Run: `uv run pytest tests/unit_tests/models/test_event.py -q`
Expected: FAIL (cannot import `Event`/`EventRef`).

- [ ] **Step 3: Add `EventRef` to `common.py`**

Append after `OrgRef`:
```python
class EventRef(VgmdbModel):
    """A lightweight pointer to an event (distinct from the full Event entity)."""

    names: LocalizedText
    id: int | None = None
    link: str | None = None
```

- [ ] **Step 4: Create `models/event.py`**

```python
"""Event entity model for vgmdb-client."""

from __future__ import annotations

from vgmdb_client.models.common import LocalizedText, PartialDate, VgmdbModel


class Event(VgmdbModel):
    """A vgmdb event (concert, convention, ...), core subset of fields.

    ``type`` is stored verbatim if shown. ``end_date`` is ``None`` for a single-day event or when
    the page shows no distinct end. Released-album / related lists are out of scope this pass.
    """

    id: int
    link: str | None = None
    names: LocalizedText
    type: str | None = None
    start_date: PartialDate | None = None
    end_date: PartialDate | None = None
    notes: str | None = None
```

- [ ] **Step 5: Export from `models/__init__.py` and top-level `__init__.py`**

In `models/__init__.py`: import `Event` from `vgmdb_client.models.event`, import `EventRef` from `vgmdb_client.models.common`, and add `"Event"`, `"EventRef"` to `__all__`.
In `src/vgmdb_client/__init__.py`: add `Event`, `EventRef` to the `from vgmdb_client.models import (...)` block and to `__all__`.

- [ ] **Step 6: Run tests + ruff/mypy**

Run: `uv run pytest tests/unit_tests/models/test_event.py -q && uv run ruff check src tests && uv run mypy`
Expected: PASS, clean.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "feat(models): add Event entity + EventRef"
```

---

## Task 2: Album.release_event field

**Files:**
- Modify: `src/vgmdb_client/models/album.py`
- Test: `tests/unit_tests/models/test_album.py` (or the existing album model test)

- [ ] **Step 1: Write failing test**

```python
def test_album_release_event_defaults_none_and_accepts_ref() -> None:
    from vgmdb_client import Album, EventRef
    from vgmdb_client.models import LocalizedText
    a = Album(id=1, titles=LocalizedText({"English": "X"}))
    assert a.release_event is None
    a2 = Album(id=1, titles=LocalizedText({"English": "X"}),
               release_event=EventRef(names=LocalizedText({"English": "E"}), id=149))
    assert a2.release_event.id == 149
```

- [ ] **Step 2: Run, verify fail**

Run: `uv run pytest -q -k release_event`
Expected: FAIL (`release_event` not a field / rejected as unknown).

- [ ] **Step 3: Add the field**

In `models/album.py`, import `EventRef` from `common`, and add to `Album` (after `notes`):
```python
    release_event: EventRef | None = None
```

- [ ] **Step 4: Run tests (full model suite stays green)**

Run: `uv run pytest tests/unit_tests/models -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(models): add additive Album.release_event"
```

---

## Task 3: Event fixtures loader + golden

**Files:**
- Modify: `tests/support/fixtures.py`
- Create: `tests/fixtures/vgmdb/events/149.json`

- [ ] **Step 1: Author the golden `149.json` BY HAND from `events/149.html`** (no parser; README rule)

```json
{
  "id": 149,
  "link": "https://vgmdb.net/event/149",
  "names": {"English": "Hakurei Shrine Reitaisai 9", "Japanese": "博麗神社例大祭（第9回）"},
  "type": null,
  "start_date": {"year": 2012, "month": 5, "day": 27},
  "end_date": null,
  "notes": null
}
```
Confirm `type`/`notes` against the rendered page before finalizing; set them if the page shows a distinct event type or notes block (leave `null` if not).

- [ ] **Step 2: Add `load_event_fixture` mirroring `load_product_fixture`**

In `tests/support/fixtures.py`, add a loader that reads `events/<id>.html` + `events/<id>.json` and returns `(html, Event.model_validate_json(...))`. Match the existing loader signature/return shape exactly.

- [ ] **Step 3: Smoke-test the loader**

```python
# in tests/unit_tests/... (or a quick check)
def test_load_event_fixture() -> None:
    from tests.support.fixtures import load_event_fixture
    html, golden = load_event_fixture(149)
    assert golden.id == 149 and "vgmdb" in html
```

Run: `uv run pytest -q -k load_event_fixture` → PASS.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "test(fixtures): event golden 149 + load_event_fixture"
```

---

## Task 4: parse_event parser

**Files:**
- Modify: `src/vgmdb_client/parsers/errors.py`, `src/vgmdb_client/parsers/__init__.py`
- Create: `src/vgmdb_client/parsers/event.py`
- Test: `tests/unit_tests/parsers/test_event.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit_tests/parsers/test_event.py
from __future__ import annotations
import pytest
from tests.support.fixtures import load_event_fixture
from vgmdb_client.parsers import parse_event
from vgmdb_client.parsers.errors import NotAnEventPageError

def test_parse_event_matches_golden() -> None:
    html, golden = load_event_fixture(149)
    assert parse_event(html) == golden

def test_parse_event_rejects_non_event_page() -> None:
    with pytest.raises(NotAnEventPageError):
        parse_event("<html><body><h1>nope</h1></body></html>")
```

- [ ] **Step 2: Run, verify fail**

Run: `uv run pytest tests/unit_tests/parsers/test_event.py -q`
Expected: FAIL (cannot import `parse_event`).

- [ ] **Step 3: Add `NotAnEventPageError`**

In `parsers/errors.py`, add (mirroring `NotAProductPageError`):
```python
class NotAnEventPageError(ParseError):
    """Raised when the HTML is not a vgmdb event page."""

    def __init__(self, message: str = "The HTML is not a vgmdb event page.") -> None:
        super().__init__(message)
```

- [ ] **Step 4: Create `parsers/event.py`**

```python
"""Event page parser (clean-room, owned selectors)."""

from __future__ import annotations

import re

from lxml.html import HtmlElement

from vgmdb_client.models import Event
from vgmdb_client.parsers import _dom
from vgmdb_client.parsers.errors import NotAnEventPageError

_EVENT_ID = re.compile(r"/event/(\d+)")


def parse_event(html: str) -> Event:
    """Parse a captured vgmdb event page into an :class:`Event` (clean-room selectors)."""
    tree = _dom.parse_tree(html)

    canonical = tree.xpath('//link[@rel="canonical"]/@href')
    match = _EVENT_ID.search(canonical[0]) if canonical else None
    if match is None:
        raise NotAnEventPageError()

    names = _dom.localized_text(_leading_group(tree.xpath('//span[@class="albumtitle"]')))
    if not names.all:
        raise NotAnEventPageError()

    start_date = _event_date(tree)
    return Event(
        id=int(match.group(1)),
        link=canonical[0],
        names=names,
        type=None,
        start_date=start_date,
        end_date=None,
        notes=None,
    )


def _leading_group(spans: list[HtmlElement]) -> list[HtmlElement]:
    """First contiguous run of language spans (one per lang) — the event's own name."""
    seen: set[str] = set()
    group: list[HtmlElement] = []
    for span in spans:
        lang = span.get("lang")
        if lang and lang in seen:
            break
        if lang:
            seen.add(lang)
        group.append(span)
    return group


def _event_date(tree: HtmlElement):  # -> PartialDate | None
    """The event's date from the first 'smallfont label' date in the header."""
    labels = tree.xpath('//span[@class="smallfont label"]')
    return _dom.partial_date(_dom.text(labels[0])) if labels else None
```
**Note:** confirm the date selector against the golden in Step 6. If `smallfont label` proves ambiguous (picks a related-album date), scope it to the event header container instead; the golden (`start_date 2012-05-27`) is the oracle. Add a `_leading_group`/date type import (`PartialDate`) and annotate `_event_date` returns `PartialDate | None`.

- [ ] **Step 5: Export `parse_event` + `NotAnEventPageError` from `parsers/__init__.py`**

- [ ] **Step 6: Run tests, iterate selectors until golden matches**

Run: `uv run pytest tests/unit_tests/parsers/test_event.py -q`
Expected: PASS (adjust `_event_date` scope if needed so the parsed `Event` equals the golden).

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "feat(parsers): add parse_event + NotAnEventPageError"
```

---

## Task 5: Album parser — release_event extraction

**Files:**
- Modify: `src/vgmdb_client/parsers/album.py`
- Modify: `tests/fixtures/vgmdb/albums/33000.json`
- Test: `tests/unit_tests/parsers/test_album.py` (extend)

- [ ] **Step 1: Update the 33000 golden** to include the expected `release_event`

```json
"release_event": {"names": {"English": "Hakurei Shrine Reitaisai 9"}, "id": 149, "link": "https://vgmdb.net/event/149"}
```
(Confirm the anchor's display name: it comes from the `title` "Released at Hakurei Shrine Reitaisai 9 (May 27, 2012)" with the leading "Released at " stripped and a trailing " (date)" stripped, OR the anchor text — verify against the HTML and match the parser rule below.)

- [ ] **Step 2: Write failing tests**

```python
def test_album_33000_has_release_event() -> None:
    from tests.support.fixtures import load_album_fixture
    from vgmdb_client.parsers import parse_album
    html, golden = load_album_fixture(33000)
    album = parse_album(html)
    assert album.release_event is not None
    assert album.release_event.id == 149
    assert album == golden

def test_album_without_release_event_is_none() -> None:
    from tests.support.fixtures import load_album_fixture
    from vgmdb_client.parsers import parse_album
    html, _ = load_album_fixture(271)
    assert parse_album(html).release_event is None
```

- [ ] **Step 3: Run, verify fail**

Run: `uv run pytest -q -k release_event`
Expected: FAIL (parser does not populate `release_event` yet; 33000 golden mismatch).

- [ ] **Step 4: Implement extraction in `parsers/album.py`**

Add a helper and call it in `parse_album` (set `release_event=_release_event(tree)`):
```python
_EVENT_ID = re.compile(r"/event/(\d+)")
_RELEASED_AT = re.compile(r"^\s*Released at\s+", re.IGNORECASE)
_TRAILING_DATE_PAREN = re.compile(r"\s*\([^)]*\)\s*$")

def _release_event(tree: HtmlElement) -> "EventRef | None":
    anchors = tree.xpath('//a[contains(@class, "link_event") and contains(@href, "/event/")]')
    if not anchors:
        return None
    anchor = anchors[0]
    href = anchor.get("href")
    eid = _EVENT_ID.search(href or "")
    title = anchor.get("title") or _dom.text(anchor)
    name = _TRAILING_DATE_PAREN.sub("", _RELEASED_AT.sub("", title)).strip()
    if not name:
        return None
    return EventRef(
        names=LocalizedText({"Japanese" if _dom.has_cjk(name) else "English": name}),
        id=int(eid.group(1)) if eid else None,
        link=_dom.absolute_url(href),
    )
```
Import `EventRef` in `parsers/album.py` from `vgmdb_client.models`.

- [ ] **Step 5: Run tests — release_event + the FULL album suite stays green**

Run: `uv run pytest tests/unit_tests/parsers -q`
Expected: PASS (existing album goldens unaffected; 33000 now matches; 271 is `None`).

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat(parsers): album release_event from link_event anchor"
```

---

## Task 6: Client get_event (sync + async)

**Files:**
- Modify: `src/vgmdb_client/client/_core.py`, `sync_client.py`, `async_client.py`
- Test: `tests/unit_tests/client/test_client.py` (extend)

- [ ] **Step 1: Write failing tests** (mirror `get_product` tests + parity)

```python
def test_get_event_returns_golden() -> None:
    from tests.support.fixtures import load_event_fixture
    from vgmdb_client import Client
    from vgmdb_client.client._core import event_path
    html, golden = load_event_fixture(149)
    client = Client(transport=StubSyncTransport({event_path(149): html}))
    assert client.get_event(149) == golden

def test_async_get_event_returns_golden() -> None:
    from tests.support.fixtures import load_event_fixture
    from vgmdb_client import AsyncClient
    from vgmdb_client.client._core import event_path
    html, golden = load_event_fixture(149)
    client = AsyncClient(transport=StubAsyncTransport({event_path(149): html}))
    assert _run(client.get_event(149)) == golden
```

- [ ] **Step 2: Run, verify fail**

Run: `uv run pytest -q -k get_event`
Expected: FAIL (no `event_path` / `get_event`).

- [ ] **Step 3: Add `event_path` to `_core.py`**

```python
def event_path(event_id: int) -> str:
    """The request path for an event page."""
    return f"/event/{event_id}"
```

- [ ] **Step 4: Add `get_event`** to `Client` and `AsyncClient` (mirror `get_product`)

Sync:
```python
    def get_event(self, event_id: int) -> Event:
        """Fetch and parse an event page."""
        return parse_event(self._transport.get(_core.event_path(event_id)))
```
Async: `async def get_event(...)` with `await`. Import `Event` from `vgmdb_client.models` and `parse_event` from `vgmdb_client.parsers` in both client modules.

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/unit_tests/client -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat(client): add get_event (sync + async)"
```

---

## Task 7: Full verification

- [ ] **Step 1: Public API surface** — confirm `from vgmdb_client import Event, EventRef` works and the public-API tests pass.

Run: `uv run pytest tests/unit_tests/client/test_client.py -q -k public_api`

- [ ] **Step 2: Full gates**

Run: `uv run ruff check src tests && uv run mypy && uv run pytest -q && uv run deptry src`
Expected: all green; no new runtime dependency.

- [ ] **Step 3: Tick the openspec `tasks.md`** for `remaining-entities` and commit.

```bash
git add -A && git commit -m "chore: tick remaining-entities tasks"
```

---

## Self-Review

- **Spec coverage:** models delta (Event ✓ T1, EventRef ✓ T1, Album.release_event ✓ T2); parsers delta (parse_event + NotAnEventPageError ✓ T4, album release_event ✓ T5); client delta (get_event sync+async ✓ T6). Fixtures prerequisite ✓ T3 (capture already done). Public API ✓ T1/T7.
- **Placeholders:** golden `type`/`notes` and the date/anchor-name selectors are flagged for confirmation against the page/golden, with the golden as the oracle — not open-ended TODOs.
- **Type consistency:** `Event`, `EventRef`, `release_event`, `event_path`, `parse_event`, `NotAnEventPageError`, `load_event_fixture` used consistently across tasks.

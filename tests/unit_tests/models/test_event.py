"""Tests for the Event entity model, EventRef, and Album.release_event."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from vgmdb_client import Album, Event, EventRef
from vgmdb_client.models import LocalizedText, PartialDate


def test_event_full() -> None:
    e = Event(
        id=149,
        link="https://vgmdb.net/event/149",
        names=LocalizedText({"English": "Hakurei Shrine Reitaisai 9"}),
        start_date=PartialDate(year=2012, month=5, day=27),
    )
    assert e.id == 149
    assert e.start_date is not None and e.start_date.year == 2012
    assert e.end_date is None


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


def test_album_release_event_defaults_none_and_accepts_ref() -> None:
    a = Album(id=1, titles=LocalizedText({"English": "X"}))
    assert a.release_event is None
    ref = EventRef(names=LocalizedText({"English": "E"}), id=149)
    a2 = Album(id=1, titles=LocalizedText({"English": "X"}), release_event=ref)
    assert a2.release_event is not None and a2.release_event.id == 149

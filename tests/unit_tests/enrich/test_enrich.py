"""Tests for the B1 deep-parse enrichment helper and backends."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from tests.support.fixtures import load_album_fixture
from vgmdb_client.enrich import (
    AlbumEnrichment,
    EnrichmentError,
    OpenAICompatibleBackend,
    backend_from_env,
    enrich_album,
)
from vgmdb_client.models import Album, Credit, Role

LLM_URL = "https://llm.test/v1/chat/completions"


def _chat_response(content: object) -> httpx.Response:
    text = content if isinstance(content, str) else json.dumps(content)
    return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


class StubBackend:
    def __init__(self, enrichment: AlbumEnrichment) -> None:
        self._enrichment = enrichment
        self.seen_raw: str | None = None

    def enrich(self, album: Album, raw_text: str) -> AlbumEnrichment:
        self.seen_raw = raw_text
        return self._enrichment


# --- overlay model + helper ---------------------------------------------------------------


def test_empty_enrichment_is_empty() -> None:
    assert AlbumEnrichment(album_id=1).is_empty is True
    assert AlbumEnrichment(album_id=1, track_credits={5: []}).is_empty is True


def test_populated_enrichment_not_empty() -> None:
    e = AlbumEnrichment(album_id=1, track_credits={10: [Credit(role=Role.COMPOSER, role_raw="Music")]})
    assert e.is_empty is False
    assert e.track_credits[10][0].role is Role.COMPOSER


def test_enrich_album_no_backend_returns_empty() -> None:
    _, album = load_album_fixture(271)
    result = enrich_album(album)
    assert isinstance(result, AlbumEnrichment)
    assert result.album_id == album.id
    assert result.is_empty is True


def test_enrich_album_uses_backend_and_notes() -> None:
    _, album = load_album_fixture(271)
    canned = AlbumEnrichment(album_id=album.id, track_credits={1: [Credit(role=Role.COMPOSER, role_raw="Composer")]})
    stub = StubBackend(canned)
    result = enrich_album(album, stub)
    assert result is canned
    assert stub.seen_raw == (album.notes or "")


# --- OpenAI-compatible backend ------------------------------------------------------------


@respx.mock
def test_openai_backend_parses_and_normalizes_roles() -> None:
    _, album = load_album_fixture(271)
    content = {
        "track_credits": {"10": [{"role_raw": "Performed by", "artists": [{"names": {"English": "MorissonPoe"}}]}]}
    }
    respx.post(LLM_URL).mock(return_value=_chat_response(content))
    backend = OpenAICompatibleBackend(url=LLM_URL, model="m", api_key="k")
    enrichment = backend.enrich(album, album.notes or "")
    credit = enrichment.track_credits[10][0]
    assert credit.role is Role.PERFORMER  # normalize_role applied by us, not the LLM
    assert credit.role_raw == "Performed by"
    assert credit.artists[0].names.default == "MorissonPoe"


@respx.mock
def test_openai_backend_non_json_content_raises() -> None:
    _, album = load_album_fixture(271)
    respx.post(LLM_URL).mock(return_value=_chat_response("not json at all"))
    with pytest.raises(EnrichmentError):
        OpenAICompatibleBackend(url=LLM_URL, model="m").enrich(album, "")


@respx.mock
def test_openai_backend_http_error_raises() -> None:
    _, album = load_album_fixture(271)
    respx.post(LLM_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(EnrichmentError):
        OpenAICompatibleBackend(url=LLM_URL, model="m").enrich(album, "")


@respx.mock
def test_openai_backend_schema_invalid_raises() -> None:
    _, album = load_album_fixture(271)
    # missing role_raw -> KeyError during build -> EnrichmentError
    respx.post(LLM_URL).mock(return_value=_chat_response({"track_credits": {"10": [{"artists": []}]}}))
    with pytest.raises(EnrichmentError):
        OpenAICompatibleBackend(url=LLM_URL, model="m").enrich(album, "")


def test_backend_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_URL", raising=False)
    assert backend_from_env() is None
    monkeypatch.setenv("LLM_URL", LLM_URL)
    monkeypatch.setenv("LLM_MODEL", "my-model")
    backend = backend_from_env()
    assert isinstance(backend, OpenAICompatibleBackend)

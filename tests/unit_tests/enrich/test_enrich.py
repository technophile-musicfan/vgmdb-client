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
    route = respx.post(LLM_URL).mock(return_value=_chat_response(content))
    backend = OpenAICompatibleBackend(url=LLM_URL, model="m", api_key="k")
    enrichment = backend.enrich(album, album.notes or "")
    credit = enrichment.track_credits[10][0]
    assert credit.role is Role.PERFORMER  # normalize_role applied by us, not the LLM
    assert credit.role_raw == "Performed by"
    assert credit.artists[0].names.default == "MorissonPoe"
    # the outgoing request carries auth, the configured model, and the album's freeform notes
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer k"
    payload = json.loads(request.content)
    assert payload["model"] == "m"
    user_message = payload["messages"][-1]["content"]
    assert (album.notes or "") in user_message


@respx.mock
def test_openai_backend_pydantic_invalid_raises() -> None:
    _, album = load_album_fixture(271)
    # "names" must be a dict; a list fails pydantic validation -> EnrichmentError (not a raw ValidationError)
    bad = {"track_credits": {"10": [{"role_raw": "Composer", "artists": [{"names": ["nope"]}]}]}}
    respx.post(LLM_URL).mock(return_value=_chat_response(bad))
    with pytest.raises(EnrichmentError):
        OpenAICompatibleBackend(url=LLM_URL, model="m").enrich(album, "")


@respx.mock
def test_openai_backend_non_json_content_raises() -> None:
    _, album = load_album_fixture(271)
    respx.post(LLM_URL).mock(return_value=_chat_response("not json at all"))
    # default max_retries=1 -> the invalid reply is retried once, then EnrichmentError.
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
    # missing role_raw -> _LlmResponse validation fails -> retried, then EnrichmentError
    respx.post(LLM_URL).mock(return_value=_chat_response({"track_credits": {"10": [{"artists": []}]}}))
    with pytest.raises(EnrichmentError):
        OpenAICompatibleBackend(url=LLM_URL, model="m").enrich(album, "")


def test_backend_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_OUTPUT_MODE", raising=False)
    assert backend_from_env() is None
    monkeypatch.setenv("LLM_URL", LLM_URL)
    monkeypatch.setenv("LLM_MODEL", "my-model")
    monkeypatch.setenv("LLM_API_KEY", "secret")
    backend = backend_from_env()
    assert isinstance(backend, OpenAICompatibleBackend)
    # the env values are actually read, not defaulted
    assert backend._url == LLM_URL
    assert backend._model == "my-model"
    assert backend._api_key == "secret"
    assert backend._output_mode == "json_object"  # default when LLM_OUTPUT_MODE unset


def test_backend_from_env_reads_output_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_URL", LLM_URL)
    monkeypatch.setenv("LLM_OUTPUT_MODE", "tool")
    assert backend_from_env()._output_mode == "tool"  # type: ignore[union-attr]
    monkeypatch.setenv("LLM_OUTPUT_MODE", "bogus")
    assert backend_from_env()._output_mode == "json_object"  # type: ignore[union-attr]  # invalid -> default


# --- LLM backend v2: prompt, output modes, retry ------------------------------------------

_VALID = {"track_credits": {"10": [{"role_raw": "Performed by", "artists": [{"names": {"English": "Kepi"}}]}]}}


def _tool_response(content: object) -> httpx.Response:
    args = content if isinstance(content, str) else json.dumps(content)
    return httpx.Response(200, json={"choices": [{"message": {"tool_calls": [{"function": {"arguments": args}}]}}]})


@respx.mock
def test_json_schema_mode_sends_schema_and_parses() -> None:
    _, album = load_album_fixture(271)
    route = respx.post(LLM_URL).mock(return_value=_chat_response(_VALID))
    backend = OpenAICompatibleBackend(url=LLM_URL, model="m", output_mode="json_schema")
    enrichment = backend.enrich(album, "")
    assert enrichment.track_credits[10][0].role is Role.PERFORMER
    payload = json.loads(route.calls.last.request.content)
    assert payload["response_format"]["type"] == "json_schema"
    assert "track_credits" in payload["response_format"]["json_schema"]["schema"]["properties"]


@respx.mock
def test_tool_mode_forces_tool_call_and_reads_arguments() -> None:
    _, album = load_album_fixture(271)
    route = respx.post(LLM_URL).mock(return_value=_tool_response(_VALID))
    backend = OpenAICompatibleBackend(url=LLM_URL, model="m", output_mode="tool")
    enrichment = backend.enrich(album, "")
    assert enrichment.track_credits[10][0].artists[0].names.default == "Kepi"
    payload = json.loads(route.calls.last.request.content)
    assert payload["tool_choice"]["function"]["name"] == "emit_enrichment"
    assert payload["tools"][0]["function"]["parameters"]["properties"]["track_credits"]


@respx.mock
def test_custom_prompt_and_template_are_sent() -> None:
    _, album = load_album_fixture(271)
    route = respx.post(LLM_URL).mock(return_value=_chat_response(_VALID))
    backend = OpenAICompatibleBackend(
        url=LLM_URL,
        model="m",
        system_prompt="CUSTOM SYSTEM",
        user_template="only notes: {notes}",
    )
    backend.enrich(album, "the notes")
    messages = json.loads(route.calls.last.request.content)["messages"]
    assert messages[0]["content"] == "CUSTOM SYSTEM"
    assert messages[1]["content"] == "only notes: the notes"


@respx.mock
def test_corrective_retry_recovers() -> None:
    _, album = load_album_fixture(271)
    route = respx.post(LLM_URL).mock(side_effect=[_chat_response("not json"), _chat_response(_VALID)])
    backend = OpenAICompatibleBackend(url=LLM_URL, model="m", max_retries=1)
    enrichment = backend.enrich(album, "")
    assert enrichment.track_credits[10][0].role is Role.PERFORMER
    assert route.call_count == 2
    # the retry appended a corrective user message
    retry_messages = json.loads(route.calls[1].request.content)["messages"]
    assert any("previous response was invalid" in m["content"] for m in retry_messages)


@respx.mock
def test_retry_exhausted_raises() -> None:
    _, album = load_album_fixture(271)
    route = respx.post(LLM_URL).mock(return_value=_chat_response("still not json"))
    backend = OpenAICompatibleBackend(url=LLM_URL, model="m", max_retries=1)
    with pytest.raises(EnrichmentError):
        backend.enrich(album, "")
    assert route.call_count == 2  # initial + one retry


@respx.mock
def test_no_retry_when_max_retries_zero() -> None:
    _, album = load_album_fixture(271)
    route = respx.post(LLM_URL).mock(return_value=_chat_response("not json"))
    backend = OpenAICompatibleBackend(url=LLM_URL, model="m", max_retries=0)
    with pytest.raises(EnrichmentError):
        backend.enrich(album, "")
    assert route.call_count == 1


def test_malformed_user_template_raises_enrichment_error() -> None:
    _, album = load_album_fixture(271)
    # a stray {ref} placeholder is not provided by the backend -> EnrichmentError, not a raw KeyError
    backend = OpenAICompatibleBackend(url=LLM_URL, model="m", user_template="notes {notes} see {ref}")
    with pytest.raises(EnrichmentError):
        backend.enrich(album, "")


@respx.mock
def test_array_style_content_is_parsed() -> None:
    _, album = load_album_fixture(271)
    # some endpoints return content as a list of typed parts rather than a bare string
    parts = [{"type": "text", "text": json.dumps(_VALID)}]
    respx.post(LLM_URL).mock(return_value=httpx.Response(200, json={"choices": [{"message": {"content": parts}}]}))
    enrichment = OpenAICompatibleBackend(url=LLM_URL, model="m").enrich(album, "")
    assert enrichment.track_credits[10][0].role is Role.PERFORMER

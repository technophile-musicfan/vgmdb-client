"""OpenAI-compatible LLM enrichment backend."""

from __future__ import annotations

import os
from typing import Any, Literal, cast, get_args

import httpx
from pydantic import BaseModel, Field, ValidationError

from vgmdb_client.enrich.errors import EnrichmentError
from vgmdb_client.enrich.models import AlbumEnrichment
from vgmdb_client.models import Album, ArtistRef, Credit, LocalizedText, normalize_role

_DEFAULT_MODEL = "gpt-4o-mini"
_DEFAULT_TIMEOUT = 30.0
_REQUEST_FAILED = "Enrichment request to the LLM endpoint failed."
_MALFORMED = "Malformed enrichment payload from the LLM endpoint."
_BAD_TEMPLATE = "Invalid user_template: expected only {tracklist} and {notes} placeholders."

OutputMode = Literal["json_object", "json_schema", "tool"]
_DEFAULT_OUTPUT_MODE: OutputMode = "json_object"
_TOOL_NAME = "emit_enrichment"

_DEFAULT_SYSTEM_PROMPT = (
    "You extract per-track credits from a vgmdb album's freeform notes. "
    "Return ONLY JSON of the form "
    '{"track_credits": {"<track number>": [{"role_raw": "<verbatim role label>", '
    '"artists": [{"names": {"English": "<name>"}}]}]}}. '
    "Use the track numbers from the tracklist. Include only credits that the notes attribute to a "
    'specific track. If none, return {"track_credits": {}}.'
)
_DEFAULT_USER_TEMPLATE = "Tracklist:\n{tracklist}\n\nNotes:\n{notes}"


class _LlmArtist(BaseModel):
    """An artist in the LLM's reply (a language->name mapping)."""

    names: dict[str, str]


class _LlmCredit(BaseModel):
    """A single credit in the LLM's reply (verbatim role label + artists)."""

    role_raw: str
    artists: list[_LlmArtist] = Field(default_factory=list)


class _LlmResponse(BaseModel):
    """The expected LLM reply shape; backs both schema derivation and reply validation."""

    track_credits: dict[str, list[_LlmCredit]] = Field(default_factory=dict)


# Derived once: the JSON Schema sent in json_schema / tool modes. ``track_credits`` is an open-keyed
# map (track number -> credits), which OpenAI strict mode cannot express, so strict is not requested.
_RESPONSE_SCHEMA = _LlmResponse.model_json_schema()


class OpenAICompatibleBackend:
    """Enrichment via an OpenAI-compatible ``/chat/completions`` endpoint.

    The prompt is customizable (``system_prompt`` / ``user_template``), the output can be requested as
    free JSON, a JSON schema, or a forced tool call (``output_mode``), every reply is validated against
    an internal response model, and an invalid reply is retried with a corrective message.
    """

    def __init__(
        self,
        url: str,
        model: str = _DEFAULT_MODEL,
        api_key: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
        *,
        output_mode: OutputMode = _DEFAULT_OUTPUT_MODE,
        system_prompt: str | None = None,
        user_template: str | None = None,
        max_retries: int = 1,
    ) -> None:
        self._url = url
        self._model = model
        self._api_key = api_key
        self._timeout = timeout
        self._output_mode = output_mode
        self._system_prompt = system_prompt if system_prompt is not None else _DEFAULT_SYSTEM_PROMPT
        self._user_template = user_template if user_template is not None else _DEFAULT_USER_TEMPLATE
        self._max_retries = max_retries

    def enrich(self, album: Album, raw_text: str) -> AlbumEnrichment:
        messages = self._build_messages(album, raw_text)
        last_error: Exception | None = None
        for _ in range(self._max_retries + 1):
            raw = self._call(messages)  # raises EnrichmentError on transport / malformed envelope
            try:
                response = _LlmResponse.model_validate_json(raw)
                return _build_enrichment(album.id, response)
            except (ValidationError, ValueError) as exc:
                last_error = exc
                messages = [*messages, _corrective_message(exc)]
        raise EnrichmentError(_MALFORMED) from last_error

    def _build_messages(self, album: Album, raw_text: str) -> list[dict[str, str]]:
        tracklist = "\n".join(
            f"{track.number}. {track.titles.default or ''}"
            for disc in album.discs
            for track in disc.tracks
            if track.number is not None
        )
        try:
            user = self._user_template.format(tracklist=tracklist, notes=raw_text)
        except (KeyError, IndexError, ValueError) as exc:
            raise EnrichmentError(_BAD_TEMPLATE) from exc
        return [{"role": "system", "content": self._system_prompt}, {"role": "user", "content": user}]

    def _mode_payload(self) -> dict[str, Any]:
        """The request fields that select the output mode."""
        if self._output_mode == "json_schema":
            schema = {"name": "enrichment", "schema": _RESPONSE_SCHEMA, "strict": False}
            return {"response_format": {"type": "json_schema", "json_schema": schema}}
        if self._output_mode == "tool":
            function = {"name": _TOOL_NAME, "description": "Return per-track credits.", "parameters": _RESPONSE_SCHEMA}
            return {
                "tools": [{"type": "function", "function": function}],
                "tool_choice": {"type": "function", "function": {"name": _TOOL_NAME}},
            }
        return {"response_format": {"type": "json_object"}}

    def _call(self, messages: list[dict[str, str]]) -> str:
        """POST the request and return the raw result string (JSON content, or tool-call arguments)."""
        payload: dict[str, Any] = {"model": self._model, "messages": messages, "temperature": 0}
        payload.update(self._mode_payload())
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        try:
            response = httpx.post(self._url, json=payload, headers=headers, timeout=self._timeout)
            response.raise_for_status()
            message = response.json()["choices"][0]["message"]
            if self._output_mode == "tool":
                return str(message["tool_calls"][0]["function"]["arguments"])
            return _content_text(message.get("content"))
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            raise EnrichmentError(_REQUEST_FAILED) from exc


def _content_text(content: Any) -> str:
    """Reduce a chat message's ``content`` to text: a plain string, or joined text parts.

    Some OpenAI-compatible endpoints return ``content`` as a list of typed parts
    (``[{"type": "text", "text": "..."}]``) rather than a bare string.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(part["text"] for part in content if isinstance(part, dict) and "text" in part)
    return ""


def _corrective_message(error: Exception) -> dict[str, str]:
    """A follow-up user message that asks the model to fix an invalid reply."""
    return {
        "role": "user",
        "content": f"Your previous response was invalid ({error}). Respond with ONLY JSON matching the schema.",
    }


def _build_enrichment(album_id: int, response: _LlmResponse) -> AlbumEnrichment:
    """Convert a validated LLM response into an AlbumEnrichment, normalizing roles ourselves.

    ``int(key)`` may raise ``ValueError`` for a non-numeric track key; that propagates to ``enrich``'s
    retry/raise loop (treated as an invalid reply).
    """
    track_credits: dict[int, list[Credit]] = {
        int(key): [
            Credit(
                role=normalize_role(credit.role_raw),
                role_raw=credit.role_raw,
                artists=[ArtistRef(names=LocalizedText(artist.names)) for artist in credit.artists],
            )
            for credit in entries
        ]
        for key, entries in response.track_credits.items()
    }
    return AlbumEnrichment(album_id=album_id, track_credits=track_credits)


def backend_from_env() -> OpenAICompatibleBackend | None:
    """Build a backend from ``LLM_URL``/``LLM_MODEL``/``LLM_API_KEY``/``LLM_OUTPUT_MODE``, else ``None``."""
    url = os.environ.get("LLM_URL")
    if not url:
        return None
    mode_raw = os.environ.get("LLM_OUTPUT_MODE", _DEFAULT_OUTPUT_MODE)
    mode = cast(OutputMode, mode_raw) if mode_raw in get_args(OutputMode) else _DEFAULT_OUTPUT_MODE
    return OpenAICompatibleBackend(
        url=url,
        model=os.environ.get("LLM_MODEL", _DEFAULT_MODEL),
        api_key=os.environ.get("LLM_API_KEY"),
        output_mode=mode,
    )

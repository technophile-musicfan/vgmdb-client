"""OpenAI-compatible LLM enrichment backend."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from vgmdb_client.enrich.errors import EnrichmentError
from vgmdb_client.enrich.models import AlbumEnrichment
from vgmdb_client.models import Album, ArtistRef, Credit, LocalizedText, normalize_role

_DEFAULT_MODEL = "gpt-4o-mini"
_DEFAULT_TIMEOUT = 30.0
_REQUEST_FAILED = "Enrichment request to the LLM endpoint failed."
_MALFORMED = "Malformed enrichment payload from the LLM endpoint."

_SYSTEM_PROMPT = (
    "You extract per-track credits from a vgmdb album's freeform notes. "
    "Return ONLY JSON of the form "
    '{"track_credits": {"<track number>": [{"role_raw": "<verbatim role label>", '
    '"artists": [{"names": {"English": "<name>"}}]}]}}. '
    "Use the track numbers from the tracklist. Include only credits that the notes attribute to a "
    'specific track. If none, return {"track_credits": {}}.'
)


class OpenAICompatibleBackend:
    """Enrichment via an OpenAI-compatible ``/chat/completions`` endpoint."""

    def __init__(
        self,
        url: str,
        model: str = _DEFAULT_MODEL,
        api_key: str | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._url = url
        self._model = model
        self._api_key = api_key
        self._timeout = timeout

    def enrich(self, album: Album, raw_text: str) -> AlbumEnrichment:
        data = self._call(self._build_messages(album, raw_text))
        return _build_enrichment(album.id, data)

    def _build_messages(self, album: Album, raw_text: str) -> list[dict[str, str]]:
        tracklist = "\n".join(
            f"{track.number}. {track.titles.default or ''}"
            for disc in album.discs
            for track in disc.tracks
            if track.number is not None
        )
        user = f"Tracklist:\n{tracklist}\n\nNotes:\n{raw_text}"
        return [{"role": "system", "content": _SYSTEM_PROMPT}, {"role": "user", "content": user}]

    def _call(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        try:
            response = httpx.post(self._url, json=payload, headers=headers, timeout=self._timeout)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed: dict[str, Any] = json.loads(content)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise EnrichmentError(_REQUEST_FAILED) from exc
        return parsed


def _build_enrichment(album_id: int, data: dict[str, Any]) -> AlbumEnrichment:
    """Turn the parsed LLM JSON into an AlbumEnrichment, normalizing roles ourselves."""
    raw = data.get("track_credits", {})
    track_credits: dict[int, list[Credit]] = {}
    try:
        for key, entries in raw.items():
            track_credits[int(key)] = [
                Credit(
                    role=normalize_role(entry["role_raw"]),
                    role_raw=entry["role_raw"],
                    artists=[
                        ArtistRef(names=LocalizedText(a["names"]), id=a.get("id"), link=a.get("link"))
                        for a in entry.get("artists", [])
                    ],
                )
                for entry in entries
            ]
        return AlbumEnrichment(album_id=album_id, track_credits=track_credits)
    except (KeyError, TypeError, ValueError) as exc:
        raise EnrichmentError(_MALFORMED) from exc


def backend_from_env() -> OpenAICompatibleBackend | None:
    """Build a backend from ``LLM_URL``/``LLM_MODEL``/``LLM_API_KEY``, or ``None`` if unset."""
    url = os.environ.get("LLM_URL")
    if not url:
        return None
    return OpenAICompatibleBackend(
        url=url,
        model=os.environ.get("LLM_MODEL", _DEFAULT_MODEL),
        api_key=os.environ.get("LLM_API_KEY"),
    )

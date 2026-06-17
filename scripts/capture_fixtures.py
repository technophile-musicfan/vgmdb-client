#!/usr/bin/env python
"""Dev-only fixture capture for vgmdb-client.

Fetches the raw HTML of every target listed in ``tests/fixtures/vgmdb/manifest.json`` via the
throttled :class:`SyncTransport` and writes it next to the manifest. It writes **raw HTML only** —
golden JSON is authored separately by hand (see ``tests/fixtures/vgmdb/README.md``).

This script is **not** part of the shipped package (the wheel only bundles ``src/vgmdb_client``) and
is **not** run in CI: it needs a live Cloudflare ``cf_clearance`` token and makes real, throttled
requests to vgmdb.net.

Usage::

    cp example.env .env        # fill in VGMDB_CF_CLEARANCE + VGMDB_USER_AGENT
    uv run python scripts/capture_fixtures.py [--overwrite] [--only album/271 search/multi-hit]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

from vgmdb_client.transport import (
    CloudflareChallengeError,
    SyncTransport,
    TransportConfig,
    TransportError,
)
from vgmdb_client.transport.config import DEFAULT_BASE_URL

ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = ROOT / "tests" / "fixtures" / "vgmdb"
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"

# Bulk capture is gentler than the transport's per-request default: a cf_clearance token
# tolerates only a limited request rate before Cloudflare re-challenges mid-batch.
DEFAULT_CAPTURE_INTERVAL = 5.0

# Manifest sections that are simple id-keyed entities: (manifest key, vgmdb URL prefix, output dir).
_ENTITY_SECTIONS = (
    ("artists", "artist", "artists"),
    ("products", "product", "products"),
    ("organizations", "org", "organizations"),
)


class CaptureError(Exception):
    """A capture could not proceed (bad config or manifest)."""


class MissingEnvError(CaptureError):
    """A required environment variable is unset."""

    def __init__(self, name: str) -> None:
        super().__init__(f"{name} is not set. Copy example.env to .env and fill it in (see example.env).")


class ManifestNotFoundError(CaptureError):
    """The fixture manifest is missing."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"manifest not found: {path}")


class UnknownTargetsError(CaptureError):
    """``--only`` referenced keys that are not in the manifest."""

    def __init__(self, keys: list[str]) -> None:
        super().__init__(f"--only keys not in manifest: {', '.join(keys)}")


class MalformedManifestError(CaptureError):
    """A manifest entry is missing a required field."""

    def __init__(self, field: str) -> None:
        super().__init__(f"manifest entry missing required field {field!r}")


class InvalidIntervalError(CaptureError):
    """The requested throttle interval is not a non-negative number."""

    def __init__(self, value: str) -> None:
        super().__init__(f"invalid --min-interval / VGMDB_MIN_INTERVAL: {value!r} (need a number >= 0)")


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MissingEnvError(name)
    return value


def _build_transport(min_interval: float) -> SyncTransport:
    config = TransportConfig(
        user_agent=_require_env("VGMDB_USER_AGENT"),
        cf_clearance=_require_env("VGMDB_CF_CLEARANCE"),
        base_url=os.environ.get("VGMDB_BASE_URL") or DEFAULT_BASE_URL,
        min_interval=min_interval,
    )
    return SyncTransport(config)


def _resolve_min_interval(arg: float | None) -> float:
    """Resolve the throttle interval from the flag, else VGMDB_MIN_INTERVAL, else the default.

    Reads the env var here (after ``load_dotenv``) so a value set in ``.env`` is honored.
    """
    if arg is not None:
        value = arg
    else:
        raw = os.environ.get("VGMDB_MIN_INTERVAL")
        if not raw:
            return DEFAULT_CAPTURE_INTERVAL
        try:
            value = float(raw)
        except ValueError as exc:
            raise InvalidIntervalError(raw) from exc
    if value < 0:
        raise InvalidIntervalError(str(value))
    return value


def _load_targets() -> list[tuple[str, str, str]]:
    """Return ``(key, request_path, output_relpath)`` for every manifest target.

    ``key`` is a stable human label (e.g. ``album/271``) used for ``--only`` and logging.
    """
    if not MANIFEST_PATH.exists():
        raise ManifestNotFoundError(MANIFEST_PATH)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    try:
        targets: list[tuple[str, str, str]] = []
        for entry in manifest.get("albums", []):
            album_id = entry["id"]
            targets.append((f"album/{album_id}", f"/album/{album_id}", f"albums/{album_id}.html"))
        for entry in manifest.get("search", []):
            slug = entry["slug"]
            path = f"/search?q={quote_plus(entry['query'])}"
            targets.append((f"search/{slug}", path, f"search/{slug}.html"))
        for section, url_prefix, out_dir in _ENTITY_SECTIONS:
            for entry in manifest.get(section, []):
                entity_id = entry["id"]
                targets.append(
                    (f"{url_prefix}/{entity_id}", f"/{url_prefix}/{entity_id}", f"{out_dir}/{entity_id}.html")
                )
    except KeyError as exc:
        raise MalformedManifestError(exc.args[0]) from exc
    return targets


def _select_targets(only: list[str] | None) -> list[tuple[str, str, str]]:
    """Load manifest targets, optionally filtered to the ``--only`` keys."""
    targets = _load_targets()
    if only:
        wanted = set(only)
        targets = [t for t in targets if t[0] in wanted]
        missing = wanted - {t[0] for t in targets}
        if missing:
            raise UnknownTargetsError(sorted(missing))
    return targets


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture raw vgmdb HTML fixtures (dev-only).")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-fetch and overwrite HTML that already exists (default: skip existing).",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="KEY",
        help="Capture only these manifest keys (e.g. album/271 search/multi-hit).",
    )
    parser.add_argument(
        "--min-interval",
        type=float,
        default=None,
        metavar="SECONDS",
        help=(
            "Minimum seconds between requests (default: VGMDB_MIN_INTERVAL or "
            f"{DEFAULT_CAPTURE_INTERVAL:g}s). Raise it if Cloudflare challenges mid-batch."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_dotenv(ROOT / ".env")
    args = _parse_args(argv)

    try:
        min_interval = _resolve_min_interval(args.min_interval)
        targets = _select_targets(args.only)
        transport = _build_transport(min_interval)
    except CaptureError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"capturing {len(targets)} target(s) at >={min_interval:g}s/request")

    captured = skipped = 0
    try:
        for key, request_path, out_relpath in targets:
            out_path = FIXTURES_DIR / out_relpath
            if out_path.exists() and not args.overwrite:
                print(f"skip   {key} (exists; use --overwrite to refetch)")
                skipped += 1
                continue
            print(f"fetch  {key} -> {request_path}")
            html = transport.get(request_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            # Write bytes (not write_text) so the captured HTML is byte-identical across OSes —
            # text mode would translate \n to \r\n on Windows and make fixtures non-reproducible.
            out_path.write_bytes(html.encode("utf-8"))
            captured += 1
    except CloudflareChallengeError:
        print(
            "error: vgmdb returned a Cloudflare challenge. Your VGMDB_CF_CLEARANCE token has "
            "likely expired — refresh it from your browser (and keep VGMDB_USER_AGENT matching "
            "that browser), then re-run.",
            file=sys.stderr,
        )
        return 3
    except TransportError as exc:
        print(f"error: transport failure: {exc!r}", file=sys.stderr)
        return 4
    finally:
        transport.close()

    print(f"\ndone: {captured} captured, {skipped} skipped, {len(targets)} targets.")
    print("Next: author golden JSON by hand from the captured HTML (see tests/fixtures/vgmdb/README.md).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

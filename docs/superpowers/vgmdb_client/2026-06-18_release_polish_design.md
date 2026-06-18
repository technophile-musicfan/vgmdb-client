# V1c Release Polish — Design

**Date:** 2026-06-18
**Status:** Design (Workflow 4 — docs/packaging/CI; no library-behavior spec delta, so `/opsx:propose` is skipped)
**Major scope:** `vgmdb_client`
**Epic:** `vgmdb-0e5.3` (V1c Release polish), under `vgmdb-0e5` (V1: complete & polished)

## Problem

vgmdb-client is feature-complete for V1 (MVP + Beta + V1a auth helper + V1b entities) but unreleased:
version is the placeholder `0.0.1`, the docs site is the cookiecutter-uv scaffold with a **broken**
API-reference stub (`docs/modules.md` = `::: vgmdb_client.foo`, which fails the strict
`mkdocs build -s` gate in `main.yml`), the README is a stub, and the release workflow publishes via a
long-lived PyPI API token. V1c makes the package publishable: real docs + README, correct packaging
metadata, a `1.0.0` version, Trusted-Publishing CI, and a verified clean-environment install.

## Scope decisions (brainstorm)

| Axis | Decision |
|------|----------|
| Cycle scope | Full release-readiness; the maintainer triggers the actual publish via a GitHub Release. |
| Version | `1.0.0` (matches "V1 complete"). Release tag MUST be `1.0.0` (no `v`); workflow hardened to strip an optional leading `v`. |
| Docs depth | Home + quickstart, task guides (client, authentication, enrichment, entities), and a real mkdocstrings API reference. |
| Publish auth | PyPI **Trusted Publishing (OIDC)** — no stored token. |
| CHANGELOG | None — the GitHub Release body serves as the 1.0.0 notes. |
| Process | Workflow 4 (no OpenSpec delta): design → plan → implement → `/code-review` → finish. No `/opsx:verify`/`/opsx:archive` (those are for spec deltas). |

## Components

### 1. Packaging metadata — `pyproject.toml`
- `version`: `0.0.1` → `1.0.0` (local source correctness; the release CI also sets it from the tag).
- Add `license = "MIT"` and the `License :: OSI Approved :: MIT License` classifier (LICENSE is MIT;
  metadata currently omits it).
- Review `description`/`keywords`; verify Homepage/Documentation/Repository URLs already point at the
  GitHub Pages / repo (they do).

### 2. README.md (PyPI long description)
Replace the stub with: one-line description, install (`pip install vgmdb-client`), a runnable
quickstart (obtain `cf_clearance`+UA via `Credentials.from_curl`, then `Client.get_album`/`search`),
feature bullets (sync+async, typed pydantic models incl. `Event`, the cf_clearance auth helper, the
optional enrichment backends), a docs link, the MIT license line, and a brief vgmdb
content/attribution + politeness/ToS note. Keep the existing badges.

### 3. Docs site (must make `mkdocs build -s` strict pass)
Pages under `docs/`:
- `index.md`: overview, install, quickstart.
- `guides/client.md`: `Client`/`AsyncClient`, all `get_*` (album, search, artist, product,
  organization, event), context-manager lifecycle, typed transport/parse errors.
- `guides/authentication.md`: the cf_clearance + matching User-Agent model, `Credentials.from_curl`
  (browser "Copy as cURL" flow), `from_credentials`/`set_credentials`, the renewal loop on
  `CloudflareChallengeError`, and the "assist, not defeat Cloudflare" boundary.
- `guides/enrichment.md`: opt-in enrichment — `RuleBasedBackend`, `OpenAICompatibleBackend`,
  `enrich_album`, `AlbumEnrichment`.
- `guides/entities.md`: the entity models incl. `Event` and `Album.release_event`.
- `reference/`: mkdocstrings API pages for the public modules (`client`, `models`, `transport`,
  `auth`, `enrich`, `parsers`) — replaces the broken `::: vgmdb_client.foo` stub.
- Update `mkdocs.yml` `nav` to match; remove `docs/modules.md`.

### 4. Release workflow — `.github/workflows/on-release-main.yml`
- **Trusted Publishing:** drop `UV_PUBLISH_TOKEN`/`secrets.PYPI_TOKEN`; add `permissions: id-token:
  write` to the `publish` job and publish via OIDC (`uv publish` trusted publishing, no token).
- **Tag→version hardening:** strip an optional leading `v` so a `1.0.0` or `v1.0.0` tag both produce
  the valid PyPI version `1.0.0`.
- Leave the `deploy-docs` job (GitHub Pages) as-is; it already runs `mkdocs build --clean`.

### 5. Local verification (acceptance: builds + clean-env install)
- `uv build` → sdist + wheel; validate metadata (`uvx twine check dist/*`).
- `uv run mkdocs build -s` (strict) passes — no broken references.
- Fresh-venv install of the built wheel + `import vgmdb_client` + a tiny offline smoke (a `Client`
  over a stub transport, or `parse_album` on a fixture) to confirm the artifact works installed.

## Maintainer handoff (the actual publish)

A checklist (the publish is outward-facing/irreversible and needs the maintainer's PyPI account):
1. On PyPI, register the Trusted Publisher (pending publisher) for `HOZHENWAI/vgmdb-client`, workflow
   `on-release-main.yml`, environment as configured.
2. Ensure the `github-pages` environment exists (Pages enabled for the repo).
3. Create a GitHub Release tagged **`1.0.0`** → CI sets the version, builds, publishes via OIDC, and
   deploys the docs.

## Out of scope

- Any library code change (V1c is docs/packaging/CI only).
- `CHANGELOG.md` (GitHub Release notes serve instead).
- The actual PyPI publish + GitHub Release creation (maintainer-triggered).
- The deferred follow-ups `vgmdb-0e5.1.4`, `vgmdb-0e5.2.8`, `vgmdb-0e5.2.9` (independent backlog).

## Testing / quality gates

`uv run mkdocs build -s`, `uv build` + `twine check`, fresh-venv install smoke, and the existing
suite (`ruff`, `mypy`, `pytest`, `deptry`) stay green. Ends in `/code-review` before merge.

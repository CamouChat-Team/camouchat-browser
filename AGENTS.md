# AGENTS.md — camouchat-browser

Instructions for AI agents (Claude, Codex, Gemini, etc.) working in this repository.

---

## Repository overview

`camouchat-browser` is a Python library and Docker base image that wraps
[Camoufox](https://camoufox.com/) (a patched Firefox) to provide stealth
browser sessions for the CamouChat ecosystem. Platform plugins such as
`camouchat-panos` depend on this package and build `FROM` its Docker image.

**Key principle:** this library is a thin orchestration layer. It does not
contain business logic — that belongs in the platform plugin. Changes here
affect every downstream plugin simultaneously.

---

## Source layout

```
src/camouchat_browser/
  browser_config.py     ← BrowserConfig dataclass; headless, locale, proxy, fingerprint
  browserforge.py       ← BrowserForge fingerprint generation and caching
  browser_logger.py     ← Structured logging setup (concurrent-log-handler)
  camoufox_browser.py   ← CamoufoxBrowser — async context manager, page lifecycle
  directory.py          ← XDG path resolution via platformdirs
  exceptions.py         ← Custom exception hierarchy
  profile_info.py       ← ProfileInfo dataclass (paths, encryption key)
  profile_manager.py    ← ProfileManager — create/load/delete profiles
  __init__.py           ← Public API surface

tests/
  docker_antidetect_smoke.py   ← 28-check anti-detection smoke test (Docker)
  docker_antidetect_report.json← Last smoke test result (auto-generated)

Dockerfile              ← Base Docker image (Debian 13 trixie, Camoufox binary baked in)
docs/docker.md          ← Docker reference — XDG design, entrypoint pattern, smoke test
```

---

## Python environment

- **Requires Python 3.11+**; tested on 3.11, 3.12, 3.13, 3.14.
- Use `uv` for dependency management (`uv.lock` is the source of truth).
- Run tests and linting inside the project `venv`:

```bash
uv run pytest tests/
uv run flake8 src/ tests/
```

---

## Code conventions

### Async-first

All public methods that touch the filesystem, network, or browser are `async`.
Blocking calls are wrapped with `asyncio.to_thread`. Never call blocking I/O
directly on the event loop.

### `BrowserConfig`

`BrowserConfig` is a frozen dataclass. The canonical way to construct it is
`BrowserConfig.from_dict(...)`. The `headless` field accepts `True`, `False`,
or `"virtual"` (Xvfb virtual display — required in Docker).

### `CamoufoxBrowser`

Not a context manager — instantiate it directly and call `get_page()`:

```python
browser = CamoufoxBrowser(config=config, profile=profile)
page = await browser.get_page()
```

`get_page()` lazily calls `get_instance()` on first use, which calls
`AsyncCamoufox(...).__aenter__()` with `persistent_context=True` and
`user_data_dir=profile.cache_dir`. Do not bypass `get_page()` — it is
what makes login sessions persist across restarts.

### XDG paths

All filesystem paths are resolved through `platformdirs` using the XDG env
vars (`XDG_DATA_HOME`, `XDG_CACHE_HOME`, `XDG_STATE_HOME`). Never hardcode
paths like `~/.local/share`. Setting these three variables in the environment
is the only mechanism that controls where data lands — including in Docker.

### Proxy handling

`BrowserConfig` accepts `proxy` as a `dict` with keys `server`, `username`
(optional), and `password` (optional). It is passed directly to Camoufox's
`launch_options`. GeoIP fingerprint matching is enabled automatically when
`proxy` is set and `geoip` is not explicitly provided.

---

## Docker image rules

The `Dockerfile` builds a Debian 13 (trixie) image. Keep these invariants:

1. **Debian 13 package names** — many packages have a `t64` suffix in trixie
   (e.g. `libasound2t64`, `libgtk-3-0t64`). Do not revert to bookworm names.
2. **Binary baked at build time** — `python -m camoufox fetch` runs during
   `docker build`. The binary lands at `$XDG_CACHE_HOME/camoufox`
   (`/opt/cache/camoufox`). Do not move or remove this step.
3. **Non-root user** — the image runs as user `app`. Any directory written
   during build that the app needs at runtime must be `chown app:app`.
4. **No `Xvfb &` in entrypoint** — Camoufox's `headless="virtual"` manages
   Xvfb internally. Only the `xvfb` apt package is needed.
5. **`shm_size: 2gb`** in all compose files — Firefox crashes in Docker with
   the default 64 MB `/dev/shm`.

---

## Smoke test

Before declaring any Docker-related change ready, run the anti-detection smoke
test inside the image:

```bash
docker run --rm --shm-size=2gb \
  -v $(pwd)/tests:/home/app/tests \
  camouchat-browser-base:latest \
  python tests/docker_antidetect_smoke.py
```

Expected: `28/28 checks passed | All critical checks OK` and exit code `0`.

The test checks:
- **Group A** — Virtual display active (`$DISPLAY`, screen dims, focus)
- **Group B** — No automation globals leaking (`webdriver`, CDP, Selenium)
- **Group C** — Fingerprint APIs return real values (canvas, WebGL, audio)
- **Group D** — External sites (ifconfig.me, httpbin, browserleaks, CreepJS, pixelscan)

---

## What NOT to do

- Do not add platform-specific logic to this library. Platform behavior lives
  in the plugin (`camouchat-panos`, etc.).
- Do not change the `BrowserConfig` field types without updating `from_dict`
  validation, the docstring, and any downstream plugin that reads the config.
- Do not hardcode `XDG_DATA_HOME` or any data path. Always go through
  `platformdirs` / `directory.py`.
- Do not add `Xvfb` startup to the Dockerfile `ENTRYPOINT` or `CMD`.
  Camoufox handles this when `headless="virtual"` is set.
- Do not use `docker compose down -v` in any test or CI script — it deletes
  the named volume and all session data.

---

## Releasing

1. Bump `version` in `pyproject.toml`.
2. Add a `CHANGELOG.md` entry.
3. Build and push the Docker image tagged with the new version:
   ```bash
   docker build -t ghcr.io/camouchat-team/camouchat-browser:<version> .
   docker push ghcr.io/camouchat-team/camouchat-browser:<version>
   ```
4. Publish to PyPI via `uv build && uv publish`.

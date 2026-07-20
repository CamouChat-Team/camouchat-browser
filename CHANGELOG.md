# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-07-16

### Added

- **Docker base image**: `Dockerfile`, `.dockerignore`, and `docs/docker.md` — pre-built image with Camoufox binary, Firefox system libraries, and Xvfb virtual display; designed for platform plugins to extend with `FROM camouchat-browser-base:latest`.
- **Anti-detection smoke test** (`tests/docker_antidetect_smoke.py`): 28 checks across four groups (virtual display, automation signals, fingerprint APIs, external sites) verifying the container is clean before deployment.
- **AGENTS.md**: AI agent instructions for any agent working in this repository (source layout, async-first rules, Docker invariants, what not to do).
- `BrowserConfig.from_dict()` now accepts `headless="virtual"` for Xvfb virtual display mode (Docker), alongside existing `True`/`False` values.
- `BrowserConfig.from_dict()` validates `enable_cache` is a `bool`; raises `ValueError` on wrong type.
- `pyproject.toml` classifiers now correctly list Python 3.11, 3.12, and 3.13 (previously only 3.14 was declared despite `requires-python = ">=3.11"`).

### Changed

- `BrowserConfig.headless` field type broadened from `bool` to `bool | str` to accommodate `"virtual"`.
- `BrowserConfig.prefs` field type broadened from `dict[str, bool]` to `dict[str, bool | int | str]`.
- `BrowserConfig.to_dict()` no longer emits a `fingerprint` stub; docstring explains the intentional omission (Fingerprint objects are not JSON-serializable; `from_dict` re-generates via BrowserForge).
- `CamoufoxBrowser.__GetBrowser__`: `AsyncCamoufox` context manager is now stored before `__aenter__` so partially-started browser subprocesses are cleaned up on `InvalidIP` retry and other launch exceptions.
- `CamoufoxBrowser.close_browser_by_profile`: exception is now logged with full traceback before returning `False` (was silently swallowed).
- `DirectoryManager.get_database_path`: removed `path.touch(exist_ok=True)` — SQLAlchemy creates the SQLite file on first connect; pre-touching an empty file caused `not a valid database` errors.
- `ProfileManager._write_metadata`: now atomic — writes to a `.json.tmp` temp file then `os.replace()`s into place, preventing corrupt JSON on process kill.
- `BrowserForge.get_fingerprint_as_dict`: fixed to use `pickle.load` (fingerprints are stored as binary pickle, not JSON); removed unused `import json`.
- Stale developer comment removed from `BrowserConfig.__str__` f-string.
- `docs/profiles.md`: corrected `encryption.is_encrypted` → `encryption.enabled` and `create_directories()` → `setup_profile_directories(platform, profile_id)`.

---

## [0.7.1] - 2026-04-21

### Added

- `ProfileInfo` now exposes `__str__` and `__repr__` for human-readable debugging output.
- `DirectoryManager.create_directories()` — single-call method to initialise all profile subdirs at once.
- Strict type and value validation added to `BrowserConfig.from_dict()` (proxy fields, prefs, addons, headless, geoip).
- `contextlib.suppress` usage for OS-level side-effects (`SetProcessDPIAware`, `os.kill`, `os.chmod`).
- `asyncio.to_thread` wrapping for all blocking file I/O inside async `ProfileManager` methods (`save_metadata`, `close_profile`).

### Changed

- `ProfileInfo` is now fully populated from `metadata.json` on load — no stale partial states.
- `ProfileManager` database credentials are now cleanly separated from path construction logic.
- `ProfileManager.delete_profile` and `close_profile` now accept only a `ProfileInfo` object (no raw IDs).
- `ProfileManager.activate_profile` parameter renamed `browser_obj` → `browser` for consistency.
- `BrowserConfig.fingerprint` field renamed from `fingerprint_obj`; now accepts a `Fingerprint` object or `dict` directly — passing `None` triggers `BrowserForge` auto-generation inside `CamoufoxBrowser`.
- `BrowserForge.get_fingerprint_as_dict` now raises with proper `from e` exception chaining (PEP 3134).
- `isinstance(obj, Fingerprint) or isinstance(obj, dict)` merged into `isinstance(obj, (Fingerprint, dict))`.
- `geoip` default auto-set via `bool(proxy)` instead of ternary expression.
- `requires-python` aligned to `>=3.11` across the package.

### Fixed

- Resolved cross-concern DB init URL regression introduced by storage decoupling.
- PID-redundancy in `CamoufoxBrowser` replaced with `profile_id`-based context map.
- `[tool.uv.sources]` removed from `pyproject.toml` — was breaking standalone CI builds outside the Antigravity workspace.
- Unit tests for `__GetBrowser__` now correctly patch `BrowserForge.get_fg` so they pass on headless Linux CI runners (no display).
- `directory.py`: `get_database_path` now correctly returns `path` instead of bare `return`.
- All `ruff` violations resolved: `SIM105`, `SIM101`, `SIM117`, `SIM210`, `B904`, `B006`, `ASYNC230`.

---

## [0.7.0] — 2026-04-15

First standalone release of `camouchat-browser`, extracted from the CamouChat monorepo. Versioning begins at `0.7.0` to reflect feature parity with the rest of the CamouChat ecosystem at the time of extraction.

### Added

- **Plugin Independence**: Extracted from the CamouChat monorepo into a standalone `camouchat-browser` package.
- **Camoufox Integration**: Full lifecycle management for [Camoufox](https://camoufox.com/) browser contexts via `CamoufoxBrowser`, including persistent context, GeoIP matching, proxy support, and humanized interaction.
- **BrowserForge Fingerprinting**: Hardware-level fingerprint generation and persistence via `BrowserForge`, with screen-size matching and cross-profile collision avoidance.
- **Profile Management**: `ProfileManager` with full CRUD lifecycle, AES-256 encryption key management, and PID-based browser tracking via `activate_profile` / `close_profile`.
- **Profile Sandboxing**: `DirectoryManager` with OS-aware path resolution for cache, media, database, and key files.
- **ProfileInfo Dataclass**: Typed snapshot model for all profile paths, encryption state, and activity status.
- **BrowserConfig**: Structured configuration via `BrowserConfig.from_dict()` and `to_dict()` for stealth settings (locale, headless, geoip, proxy, prefs, addons).
- **Exceptions**: `BrowserException` inheriting from `CamouChatError` for consistent ecosystem-wide error handling.
- **Documentation**: Created `docs/` with dedicated guides for `browser_config`, `camoufox_browser`, `BrowserForge`, and `profiles`.
- **README**: Professional README with Quick Start, installation (`uv` + `pip`), camoufox fetch instructions, docs links, and ethics disclaimer.

### Changed

- **pyproject.toml**: Added `Documentation` URL, expanded keywords and classifiers for improved PyPI SEO.

---

## [0.6.0] — 2026-03-20

_Note: Prior to 0.7.0, browser management was part of the unified CamouChat monorepo. See [camouchat-core CHANGELOG](https://github.com/CamouChat-Team/camouchat-core/blob/main/CHANGELOG.md) for full pre-extraction history._

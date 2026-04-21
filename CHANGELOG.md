# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

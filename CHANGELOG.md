# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.1] - unreleased

### Added

- Added missing __str__ and __repr__ methods to ProfileInfo dataclass.
- directory now have create_directories direct create point.
- added safe checks & validations in BrowserConfig from_dict method.

### Changed

- ProfileInfo gets full data now from metadata dictionary. 
- ProfileManager now also adds More database clean & safe credentials.
- delete_profile, close_profile now takes only ProfileInfo object as a parameter
- renaming of browser_obj -> browser in activte_profile
- BrowserConfig.fingerprint_obj is now fingerprint renamed and expects direct fingerprint instead of obj passing -> None passed in camoufoxBrowser makes it call default.

### Fixed

- Cross Concerned of db init urls in the profileManager brought by older code separation is resolved
- pid redundancy to profile_id based browser closing in CamoufoxBrowser is resolved
- fix test cases & scripts

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

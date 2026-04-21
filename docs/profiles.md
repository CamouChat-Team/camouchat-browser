# Profile Management

The `ProfileManager` is the central authority for managing browser sessions, data isolation, and encryption in `camouchat-browser`. All profile operations are **async-first** — blocking I/O is wrapped in `asyncio.to_thread` to prevent event-loop stalls.

## Core Classes

### `ProfileManager`

Handles the full lifecycle of individual browser profiles. Each profile is a sandboxed directory containing its own cookies, cache, fingerprints, and databases.

**Key Methods:**

| Method | Description |
|---|---|
| `create_profile(platform, profile_id, db_credentials)` | Initialises a new sandbox for a platform user. |
| `get_profile(platform, profile_id)` | Returns a `ProfileInfo` for an existing profile. |
| `list_profiles(platform=None)` | Lists profiles across one or all platforms. |
| `activate_profile(platform, profile_id, browser)` | Marks a profile active and links it to the browser context. |
| `close_profile(profile, force=False)` | Safely shuts down the browser and releases locks. |
| `delete_profile(profile, force=False)` | Completely wipes profile data from disk. |

> **v0.7.1:** `delete_profile` and `close_profile` accept a `ProfileInfo` object. `activate_profile` renamed `browser_obj` → `browser`. Note: `get_profile` and `activate_profile` still take raw `platform` + `profile_id` — only the lifecycle-ending methods use `ProfileInfo`.

### `ProfileInfo`

A fully-populated dataclass snapshot of a profile's state, constructed via `ProfileInfo.from_metadata()` from the profile's `metadata.json`. All fields are read-only at runtime — mutating them does not persist to disk.

#### Identity Fields

| Field | Type | Description |
|---|---|---|
| `profile_id` | `str` | Unique identifier for this profile. |
| `platform` | `Platform` | Target platform (e.g., `Platform.WHATSAPP`). |
| `version` | `str` | Profile schema version (for migrations). |
| `created_at` | `str` | ISO timestamp of profile creation. |
| `last_used` | `str` | ISO timestamp of last activation. |

#### Path Fields

| Field | Type | Description |
|---|---|---|
| `profile_dir` | `Path` | Root sandbox directory for this profile. |
| `fingerprint_path` | `Path` | Path to `fingerprint.pkl` (BrowserForge cache). |
| `cache_dir` | `Path` | Camoufox persistent browser session data. |
| `media_dir` | `Path` | Root media storage directory. |
| `media_images_dir` | `Path` | Received images storage path. |
| `media_videos_dir` | `Path` | Received videos storage path. |
| `media_voice_dir` | `Path` | Received voice notes storage path. |
| `media_documents_dir` | `Path` | Received documents storage path. |

#### Database Credential Fields

| Field | Type | Description |
|---|---|---|
| `db_type` | `str \| None` | Storage backend type (e.g., `"sqlite"`, `"postgresql"`). |
| `database_path` | `Path \| None` | Absolute path to local SQLite file (if applicable). |
| `database_name` | `str \| None` | Database name (used for remote backends). |
| `username` | `str \| None` | DB username (remote backends only). |
| `password` | `str \| None` | DB password (remote backends only). |
| `host` | `str \| None` | DB host (remote backends only). |
| `port` | `int \| None` | DB port (remote backends only). |

#### Runtime State Fields

| Field | Type | Description |
|---|---|---|
| `is_active` | `bool` | Whether the profile has an active browser session. |
| `last_active_pid` | `int \| None` | PID of the last process that activated this profile. |

#### Security Fields

| Field | Type | Description |
|---|---|---|
| `encryption` | `dict` | Raw encryption config dict from `metadata.json`. Contains `is_encrypted` flag and key metadata. |


### `DirectoryManager`

Internal utility that resolves consistent, OS-aware paths using `platformdirs`. Exposes `create_directories()` to initialise all subdirectories for a profile in a single call.

## Encryption Management

`ProfileManager` handles secure AES-256 key storage for message encryption.

| Method | Description |
|---|---|
| `enable_encryption(platform, profile_id)` | Generates a 32-byte key and saves it to `encryption.key`. |
| `get_key(platform, profile_id)` | Returns the raw key bytes. |
| `disable_encryption(platform, profile_id)` | Permanently wipes the key file. ⚠️ Irrecoverable. |

## Directory Structure

Profiles are stored in the OS user data directory under:

```
CamouChat/platforms/<platform>/<profile_id>/
├── metadata.json       # Configuration and status snapshot
├── encryption.key      # AES-256 key (if encryption enabled)
├── messages.db         # Message history (SQLAlchemy)
├── fingerprint.pkl     # Cached BrowserForge fingerprint
└── cache/              # Camoufox browser session data
```

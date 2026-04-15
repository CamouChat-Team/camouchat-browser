# Profile Management

The `ProfileManager` is the central authority for managing browser sessions, data isolation, and encryption in `camouchat-browser`.

## Core Classes

### `ProfileManager`
Handles the lifecycle of individual browser profiles. Each profile is a sandboxed directory containing its own cookies, cache, fingerprints, and databases.

**Key Methods:**
- **`create_profile(platform, profile_id, ...)`**: Initializes a new sandbox for a specific platform user.
- **`get_profile(platform, profile_id)`**: Retrieves a `ProfileInfo` object for an existing profile.
- **`list_profiles(platform=None)`**: Lists all profiles across one or all platforms.
- **`activate_profile(platform, profile_id, browser_obj)`**: Marks a profile as active and links it to a PID.
- **`close_profile(platform, profile_id, force=False)`**: Safely shuts down the browser and releases locks.
- **`delete_profile(platform, profile_id, force=False)`**: Completely wipes profile data from disk.

### `ProfileInfo`
A dataclass representing a snapshot of a profile's state. It provides easy access to:
- Profile paths (cache, media, database)
- Encryption status
- Activation status and PID

### `DirectoryManager`
An internal utility used by the manager to resolve consistent paths across different Operating Systems using `platformdirs`.

## Encryption Management

`ProfileManager` also handles secure key storage for message encryption.

- **`enable_encryption(platform, profile_id)`**: Generates a 32-byte AES-256 key and saves it to a protected file (`encryption.key`).
- **`get_key(platform, profile_id)`**: Retrieves the raw key for use in a `MessageProcessor`.
- **`disable_encryption(platform, profile_id)`**: Permanently wipes the key file (Caution: data becomes irrecoverable).

## Directory Structure
Profiles are stored in the user's data directory (OS-specific) under:
`CamouChat/platforms/<platform>/<profile_id>/`
- `metadata.json`: Configuration and status.
- `encryption.key`: AES key (if enabled).
- `messages.db`: Message history.
- `fingerprint.pkl`: Cached [BrowserForge](https://github.com/CamouChat-Team/camouchat-browser/blob/main/docs/BrowserForge.md) fingerprint.
- `cache/`: Browser session data.

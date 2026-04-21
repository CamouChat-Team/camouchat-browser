# Browser Configuration

`camouchat-browser` uses a structured configuration system via the `BrowserConfig` dataclass. It allows fine-tuned control over stealth behaviour, proxy routing, and fingerprint injection for the underlying [Camoufox](https://camoufox.com/) instance.

## Code Overview

```python
from camouchat_browser import BrowserConfig
from camouchat_core import Platform

config = BrowserConfig.from_dict({
    "platform": Platform.WHATSAPP,   # Required
    "locale": "en-US",               # Default: "en-US"
    "enable_cache": False,           # Default: False
    "headless": True,                # Default: False
    "fingerprint": None,             # None → BrowserForge auto-generates
    "geoip": True,                   # Default: auto (True if proxy provided)
    "proxy": {                       # Optional
        "server": "http://host:port",
        "username": "user",          # Optional
        "password": "pass"           # Optional
    },
    "prefs": {"javascript.enabled": True},  # Firefox prefs dict
    "addons": ["/path/to/ext.xpi"]          # Extension paths
})
```

> **Note (v0.7.1):** `fingerprint_obj` has been renamed to `fingerprint`. Pass a `Fingerprint` object, a `dict`, or `None`. When `None`, `CamoufoxBrowser` automatically calls `BrowserForge.get_fg()` to generate one.

## Methods

### `from_dict(data: dict) → BrowserConfig`

Class method that validates and constructs a `BrowserConfig` from a dictionary.

- **Raises `ValueError`** if `platform` is missing or not a `Platform` instance.
- **Raises `ValueError`** if `proxy` fields are malformed.
- Sensible defaults applied for `locale`, `headless`, `geoip`, `prefs`, and `addons`.

```python
config = BrowserConfig.from_dict(config_dict)
```

### `to_dict() → dict`

Serializes the configuration back to a dictionary. Useful for logging or persistence.

```python
data = config.to_dict()
```

## Integration with Camoufox

All `BrowserConfig` fields are passed directly to the Camoufox `launch_options()` call. For advanced settings like `prefs` or `geoip`, refer to the [Camoufox Documentation](https://camoufox.com/).

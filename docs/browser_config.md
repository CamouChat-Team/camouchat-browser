# Browser Configuration

`camouchat-browser` uses a robust configuration system via the `BrowserConfig` class. This allows for fine-tuned control over the stealth and behavior of the underlying [Camoufox](https://camoufox.com/) instances.

## Code Overview

Public APIs are exposed directly for ease of use.

```python
from camouchat_browser import BrowserConfig, BrowserForge
from camouchat_core import Platform

# Define your configuration
config_dict = {
    "platform": Platform.WHATSAPP,     # Required for ProfileManager
    "locale": "en-US",                # Default: en-US
    "enable_cache": False,            # Toggle internal caching
    "headless": True,                 # Default: False
    "fingerprint_obj": BrowserForge(), # Core fingerprint manager
    "geoip": True,                    # Enable automated GeoIP spoofing
    "proxy": {},                      # Proxy server settings (dict)
    "prefs": {},                      # Firefox user preferences
    "addons": []                      # List of extension paths
}

# Cast to BrowserConfig object
config = BrowserConfig.from_dict(data=config_dict)
```

## Methods

### `from_dict(data: dict)`
A class method used to initialize a configuration from a dictionary. Validates types and provides defaults.

**Usage:**
```python
config = BrowserConfig.from_dict(config_dict)
```

### `to_dict()`
Serializes the current configuration back into a dictionary format. Useful for saving settings or logging.

**Usage:**
```python
data = config.to_dict()
```

## Integration with Camoufox

Most parameters in `BrowserConfig` are passed directly to the [Camoufox](https://camoufox.com/) launch options. For a deep dive into advanced settings like `prefs` or `geoip`, refer to the official [Camoufox Documentation](https://camoufox.com/).
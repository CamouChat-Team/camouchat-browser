# BrowserForge Integration

The `BrowserForge` module in `camouchat-browser` manages hardware and browser fingerprinting to ensure each profile has a unique, consistent, and authentic identity.

## Overview

We use [browserforge](https://github.com/thefrop/browserforge) to generate high-quality fingerprints that spoof:
- Navigator properties (User Agent, Platform, Languages)
- Screen resolution and Color depth
- Hardware concurrency and Device memory
- WebGL and Canvas fingerprints

## Fingerprint Persistence

To avoid detection, fingerprints are tied to specific profiles. When a new profile is created, a unique fingerprint is generated and saved. Subsequent launches of the same profile will reuse the cached fingerprint.

## Core API

### `BrowserForge` Class

Initializes the fingerprint generator and handles loading/saving logic.

```python
from camouchat_browser import BrowserForge

bf = BrowserForge()
fg = bf.get_fg(profile=my_profile)
```

- **`get_fg(profile)`**: Retrieves the cached fingerprint for a profile or generates a new one if it doesn't exist.

## Why it matters

Sophisticated anti-bot systems check for consistency between your IP, Timezone, and Browser Fingerprint. By combining `BrowserForge` with [Camoufox](https://camoufox.com/), we provide a unified stealth layer that bypasses most modern fingerprinting techniques.

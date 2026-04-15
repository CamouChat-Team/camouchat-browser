# Camoufox Browser

The `CamoufoxBrowser` class is a high-level wrapper around the [Camoufox](https://camoufox.com/) engine, optimized for anti-detection and resource management.

## Features

- **Anti-Detection**: Transparently handles TLS-fingerprinting, WebGL spoofing, and font enumeration.
- **Session Persistence**: Automates the management of Playwright's persistent contexts.
- **IP Protection**: Built-in retry mechanism for invalid proxy/IP configurations.
- **Page Recycling**: Automatically searches for and reuses blank pages before creating new ones.

## Usage

### Initialization
Requires a `BrowserConfig` for settings and a `ProfileInfo` for session data.

```python
from camouchat_browser import CamoufoxBrowser

browser = CamoufoxBrowser(config=config, profile=profile)
```

### Getting a Page
Use `get_page()` to retrieve a ready-to-use Playwright `Page` object.

```python
page = await browser.get_page()
await page.goto("https://google.com")
```

### Lifecycle Management
The manager tracks browser PIDs globally. You can close a specific browser instance using its PID:

```python
await CamoufoxBrowser.close_browser_by_pid(pid)
```

## Anti-Detection Settings
By default, the following are enabled:
- **Humanize**: Smooths mouse movements and randomizes typing speeds.
- **GeoIP Spoofing**: Matches browser timezone and coordinates to the proxy IP.
- **Fingerprint Injection**: Injects authentic [BrowserForge](https://github.com/CamouChat-Team/camouchat-browser/blob/main/docs/BrowserForge.md) fingerprints into the browser context.

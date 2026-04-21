# CamouChat Browser 🦊

A high-performance, stealth-oriented browser orchestration layer designed for the CamouChat ecosystem. Built on top of [Camoufox](https://camoufox.com/), it provides advanced anti-detection capabilities, hardware-level fingerprint spoofing, and robust session management.

## Key Features

- **Advanced Stealth**: Powered by [Camoufox](https://camoufox.com/) for industry-leading anti-bot bypass.
- **Fingerprint Spoofing**: Deep integration with `browserforge` for authentic hardware and software headers.
- **Session Isolation**: Automated profile management with persistent storage for cookies and local data.
- **GeoIP & Proxy Ready**: Built-in support for residential proxies and automated GeoIP matching.
- **Humanized Interaction**: Smooth mouse movements and typing patterns to maintain high stealth scores.
- **Async-First Architecture**: All blocking I/O is wrapped in `asyncio.to_thread` — zero event-loop blocking.
- **Python 3.11+**: Compatible with Python 3.11, 3.12, 3.13, and 3.14.

## Installation

Add to your project using `uv`:

```bash
uv add camouchat-browser
```

Or with `pip`:

```bash
pip install camouchat-browser
```

After installing, fetch the Camoufox browser binary:

```bash
camoufox fetch
```

## Quick Start

```python
from camouchat_browser import BrowserConfig, CamoufoxBrowser, ProfileManager
from camouchat_core import Platform

# 1. Setup Configuration
config = BrowserConfig.from_dict({
    "platform": Platform.WHATSAPP,
    "headless": False,
    "locale": "en-US",
    # fingerprint=None → BrowserForge auto-generates one
})

# 2. Manage Profiles
pm = ProfileManager(platform=Platform.WHATSAPP)
profile = pm.get_profile(platform=Platform.WHATSAPP, profile_id="stealth_user_1")

# 3. Launch Browser
browser = CamoufoxBrowser(config=config, profile=profile)
page = await browser.get_page()

await page.goto("https://check.camoufox.com")
```

## Documentation

- [Browser Configuration](https://github.com/CamouChat-Team/camouchat-browser/blob/main/docs/browser_config.md) — Finetuning stealth settings.
- [Browser Engine](https://github.com/CamouChat-Team/camouchat-browser/blob/main/docs/camoufox_browser.md) — Deep dive into Camoufox integration.
- [Profile Management](https://github.com/CamouChat-Team/camouchat-browser/blob/main/docs/profiles.md) — Managing sandboxes and encryption.
- [Fingerprinting](https://github.com/CamouChat-Team/camouchat-browser/blob/main/docs/BrowserForge.md) — Hardware-level spoofing logic.
- [CHANGELOG](https://github.com/CamouChat-Team/camouchat-browser/blob/main/CHANGELOG.md) — Full release history.

## Roadmap

- 🐳 **Docker Containerization**: Full headless Docker image with Xvfb, Camoufox binaries, and proxy-routing pre-configured out of the box (Targeting v0.8.0).

## ⚖️ Security & Ethics

CamouChat's strict policy regarding acceptable automation, anti-spam, and stealth disclaimers can be found in our central ecosystem hub:

👉 **[SECURITY.md](https://github.com/CamouChat-Team/CamouChat/blob/main/SECURITY.md)**

## License

MIT License. See [LICENSE](LICENSE) for details.

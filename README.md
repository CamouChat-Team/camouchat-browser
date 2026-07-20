# CamouChat Browser 🦊

A high-performance, stealth-oriented browser orchestration layer for the CamouChat ecosystem. Built on top of [Camoufox](https://camoufox.com/), it provides advanced anti-detection capabilities, hardware-level fingerprint spoofing, persistent session management, and a production-ready Docker base image.

<p align="center">
  <a href="https://pypi.org/project/camouchat-browser/">
      <img src="https://img.shields.io/badge/PyPI-camouchat--browser-green" alt="PyPI" />
  </a>
  <a href="https://pepy.tech/projects/camouchat-browser">
      <img src="https://static.pepy.tech/personalized-badge/camouchat-browser?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads" alt="PyPI Downloads" />
  </a>
  <a href="https://opensource.org/licenses/MIT">
      <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
  </a>
  <a href="https://github.com/CamouChat-Team/camouchat-browser/blob/main/docs/docker.md">
      <img src="https://img.shields.io/badge/Docker-base%20image-blue?logo=docker" alt="Docker" />
  </a>
</p>

## Key Features

- **Advanced Stealth**: Powered by [Camoufox](https://camoufox.com/) for industry-leading anti-bot bypass.
- **Fingerprint Spoofing**: Deep integration with `browserforge` for authentic hardware and software headers.
- **Session Isolation**: Automated profile management with persistent storage for cookies and local data.
- **GeoIP & Proxy Ready**: Built-in support for residential proxies and automated GeoIP matching.
- **Humanized Interaction**: Smooth mouse movements and typing patterns to maintain high stealth scores.
- **Docker Base Image**: Pre-built image with Camoufox binary baked in, Xvfb virtual display, and XDG volume mounts — ready for headless server deployment.
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

# 2. Load or create a profile (session, fingerprint, encryption key)
pm = ProfileManager()
profile = pm.get_profile(platform=Platform.WHATSAPP, profile_id="stealth_user_1")

# 3. Launch the browser and get a page
browser = CamoufoxBrowser(config=config, profile=profile)
page = await browser.get_page()

await page.goto("https://check.camoufox.com")
```

## Docker

`camouchat-browser` ships a Docker base image with the Camoufox browser binary, all Firefox system libraries, and a virtual X display pre-configured. Platform plugins (like `camouchat-panos`) build `FROM` this image instead of repeating the heavy setup themselves.

### Architecture

```
camouchat-browser-base   ← this image
  Firefox system libs (libgtk, libnss, libx11 …)
  Xvfb + xclip
  Camoufox binary at /opt/cache/camoufox
  camouchat-core + camouchat-browser installed
        ↓  FROM
camouchat-whatsapp          ← your bot / plugin image
  adds plugin package + app code
  mounts /data volume for session persistence
```

### Build the base image

```bash
cd camouchat-browser

# From PyPI (stable)
docker build -t camouchat-browser-base:latest .

# From dev branch (git source)
docker build \
  --build-arg CORE_REF="git+https://github.com/CamouChat-Team/camouchat-core@dev" \
  --build-arg BROWSER_REF="git+https://github.com/CamouChat-Team/camouchat-browser@dev" \
  -t camouchat-browser-base:dev .
```

### Use `headless="virtual"` in your app

Pass `headless="virtual"` to `BrowserConfig` to activate the Xvfb virtual display. Camoufox manages the display process internally — no shell entrypoint wrapper or manual `Xvfb &` required.

```python
import os
from camouchat_browser import BrowserConfig
from camouchat_core import Platform

config = BrowserConfig.from_dict({
    "platform": Platform.WHATSAPP,
    "headless": os.getenv("HEADLESS", "virtual"),  # "virtual" | True | False
    "locale": "en-US",
})
```

### Session persistence

All state — login cookies, encryption keys, fingerprints, and the SQLite database — resolves through the XDG Base Directory Specification. Set the three XDG variables to subdirectories of a named Docker volume and everything persists across `docker compose down/up` automatically:

```yaml
# docker-compose.yml (consumer image)
services:
  bot:
    image: my-plugin:latest
    shm_size: '2gb'          # Firefox needs >= 256 MB shared memory
    volumes:
      - bot-data:/data
    environment:
      XDG_DATA_HOME:  /data/share
      XDG_CACHE_HOME: /data/cache   # Camoufox binary lives here at runtime
      XDG_STATE_HOME: /data/state

volumes:
  bot-data:
```

On first boot the entrypoint copies the Camoufox binary from `/opt/cache/camoufox` (baked into the image) to `/data/cache/camoufox` (the volume), so nothing is re-downloaded on restart.

### Anti-detection smoke test

A built-in smoke test verifies the container is not leaking automation signals before you deploy:

```bash
docker run --rm --shm-size=2gb \
  -v $(pwd)/tests:/home/app/tests \
  camouchat-browser-base:latest \
  python tests/docker_antidetect_smoke.py
```

The test runs 28 checks across four groups and exits `0` on a clean result:

| Group | What is checked |
|---|---|
| A — Virtual display | Screen dimensions, color depth, `$DISPLAY`, focus, `visibilityState` |
| B — Automation signals | `navigator.webdriver`, CDP globals, Selenium/Playwright/Nightmare.js leaks |
| C — Fingerprint APIs | Canvas non-blank, WebGL renderer not SwiftShader, AudioContext, platform spoof |
| D — External sites | ifconfig.me connectivity, User-Agent on httpbin, browserleaks.com, CreepJS, pixelscan.net |

### Publishing to a registry

```bash
docker tag camouchat-browser-base:latest \
  ghcr.io/camouchat-team/camouchat-browser:0.7.1

docker push ghcr.io/camouchat-team/camouchat-browser:0.7.1
```

Consuming images then reference:

```dockerfile
FROM ghcr.io/camouchat-team/camouchat-browser:0.7.1
```

See [docs/docker.md](https://github.com/CamouChat-Team/camouchat-browser/blob/main/docs/docker.md) for the full reference.

## Documentation

- [Browser Configuration](https://github.com/CamouChat-Team/camouchat-browser/blob/main/docs/browser_config.md) — Finetuning stealth settings.
- [Browser Engine](https://github.com/CamouChat-Team/camouchat-browser/blob/main/docs/camoufox_browser.md) — Deep dive into Camoufox integration.
- [Profile Management](https://github.com/CamouChat-Team/camouchat-browser/blob/main/docs/profiles.md) — Managing sandboxes and encryption.
- [Fingerprinting](https://github.com/CamouChat-Team/camouchat-browser/blob/main/docs/BrowserForge.md) — Hardware-level spoofing logic.
- [Docker Setup](https://github.com/CamouChat-Team/camouchat-browser/blob/main/docs/docker.md) — Base image reference, XDG volume design, registry publishing.
- [CHANGELOG](https://github.com/CamouChat-Team/camouchat-browser/blob/main/CHANGELOG.md) — Full release history.

## ⚖️ Security & Ethics

CamouChat's strict policy regarding acceptable automation, anti-spam, and stealth disclaimers can be found in our central ecosystem hub:

👉 **[SECURITY.md](https://github.com/CamouChat-Team/CamouChat/blob/main/SECURITY.md)**

## License

MIT License. See [LICENSE](LICENSE) for details.

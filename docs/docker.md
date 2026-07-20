# Docker — camouchat-browser base image

`camouchat-browser` ships a Docker base image that bakes the Camoufox stealth
browser and all its system dependencies into a single reusable layer. Platform
plugins (like `camouchat-panos`) build `FROM` this image instead of repeating
the heavy setup themselves.

---

## What the image provides

| Component | Detail |
|---|---|
| Base OS | `python:3.12-slim` — Debian 13 (trixie) |
| Firefox system libs | `libgtk-3-0t64`, `libnss3`, `libx11-6`, `libavcodec61`, and ~20 others (trixie naming) |
| Virtual framebuffer | `xvfb` — managed internally by Camoufox via `headless="virtual"` |
| Clipboard backend | `xclip` — required by pyperclip when `$DISPLAY` is active |
| Fonts | `fonts-liberation`, `fonts-noto-color-emoji` |
| Camoufox binary | Baked into the image at `/opt/cache/camoufox` at build time |
| Python packages | `camouchat-core` and `camouchat-browser` installed from PyPI |
| Runtime user | Non-root `app` user; `/opt/cache`, `/opt/share`, `/opt/state` are `chown`-ed to it |

---

## Environment variables

These are set in the image and inherited by all consuming images:

| Variable | Image default | Runtime override | Purpose |
|---|---|---|---|
| `XDG_CACHE_HOME` | `/opt/cache` | `/data/cache` | Camoufox binary location; must match between build and runtime |
| `XDG_DATA_HOME` | `/opt/share` | `/data/share` | platformdirs data root (profiles, SQLite DB, media) |
| `XDG_STATE_HOME` | `/opt/state` | `/data/state` | platformdirs state/log root |

> **Critical:** the Camoufox binary is fetched at build time and lands at
> `$XDG_CACHE_HOME/camoufox` (`/opt/cache/camoufox`). At runtime you will
> typically mount a volume at `/data` and set `XDG_CACHE_HOME=/data/cache`.
> The entrypoint of the consuming image must copy the binary from
> `/opt/cache/camoufox` → `/data/cache/camoufox` on first boot.

---

## Build the base image

```bash
cd camouchat-browser

# Stable — installs from PyPI
docker build -t camouchat-browser-base:latest .

# Development — installs from git dev branch
docker build \
  --build-arg CORE_REF="git+https://github.com/CamouChat-Team/camouchat-core@dev" \
  --build-arg BROWSER_REF="git+https://github.com/CamouChat-Team/camouchat-browser@dev" \
  -t camouchat-browser-base:dev .
```

Build time is dominated by `python -m camoufox fetch` (~200 MB Firefox
download). Subsequent builds are cached as long as the pip install layer
is unchanged.

---

## Using `headless="virtual"` in your app

Pass `headless="virtual"` to `BrowserConfig`. Camoufox's `VirtualDisplay`
class spawns Xvfb, exports `$DISPLAY`, and tears it down on exit — no shell
entrypoint wrapper or manual `Xvfb &` required.

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

Valid `headless` values:

| Value | Effect |
|---|---|
| `"virtual"` | Camoufox spawns its own Xvfb — use in Docker |
| `False` | Opens a real visible window — requires a real display |
| `True` | Native Firefox headless — more fingerprintable, avoid if possible |

---

## Consuming image pattern

A minimal `Dockerfile` for a plugin built on top of this image:

```dockerfile
FROM camouchat-browser-base:latest

# Switch to root to install the plugin package, then back to app
USER root
RUN pip install camouchat-panos
USER app

# Route all XDG dirs to the /data volume at runtime
ENV XDG_DATA_HOME=/data/share \
    XDG_CACHE_HOME=/data/cache \
    XDG_STATE_HOME=/data/state

COPY --chown=app:app app/ /home/app/app/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["python", "app/main.py"]
```

Entrypoint (`entrypoint.sh`) — copies the binary on first boot, then execs the app:

```bash
#!/bin/bash
set -e

BINARY_SRC="/opt/cache/camoufox"
BINARY_DST="${XDG_CACHE_HOME:-/data/cache}/camoufox"

if [ -d "${BINARY_SRC}" ] && [ ! -d "${BINARY_DST}" ]; then
    echo "[entrypoint] First boot: copying Camoufox binary to volume..."
    mkdir -p "$(dirname "${BINARY_DST}")"
    cp -r "${BINARY_SRC}" "${BINARY_DST}"
fi

mkdir -p \
    "${XDG_DATA_HOME:-/data/share}" \
    "${XDG_CACHE_HOME:-/data/cache}" \
    "${XDG_STATE_HOME:-/data/state}"

exec "$@"
```

---

## Session persistence

Everything that keeps a user logged in — cookies, encryption keys, fingerprints,
and the SQLite database — resolves through `platformdirs` using the XDG variables.
Set those variables to subdirectories of a named Docker volume and all state
survives `docker compose down/up`:

```yaml
services:
  bot:
    image: my-plugin:latest
    shm_size: '2gb'        # Firefox crashes with Docker's default 64 MB /dev/shm
    volumes:
      - bot-data:/data
    environment:
      XDG_DATA_HOME:  /data/share
      XDG_CACHE_HOME: /data/cache
      XDG_STATE_HOME: /data/state
    restart: unless-stopped

volumes:
  bot-data:
```

What lives in the volume:

```
/data/
  share/CamouChat/platforms/<platform>/<profile_id>/
    metadata.json       ← profile settings
    encryption.key      ← AES-256 key (chmod 600)
    fingerprint.pkl     ← BrowserForge fingerprint
    cache/              ← Camoufox persistent_context — login session cookies
    messages.db         ← SQLite message database
    media/              ← downloaded media
  cache/camoufox/       ← Camoufox browser binary (copied from image on first boot)
  state/CamouChat/log/  ← application logs
```

---

## Anti-detection smoke test

Run the built-in smoke test inside the image to confirm no automation signals
are leaking before you deploy:

```bash
docker run --rm --shm-size=2gb \
  -v $(pwd)/tests:/home/app/tests \
  camouchat-browser-base:latest \
  python tests/docker_antidetect_smoke.py
```

The test performs 28 checks across four groups and exits `0` on a clean result:

| Group | Checks |
|---|---|
| A — Virtual display | Screen dimensions, color depth, `$DISPLAY`, window focus, `visibilityState` |
| B — Automation signals | `navigator.webdriver`, CDP globals, Selenium/Playwright/Nightmare.js globals |
| C — Fingerprint APIs | Canvas non-blank, WebGL renderer not SwiftShader, AudioContext, platform spoof |
| D — External sites | Connectivity, User-Agent, browserleaks.com, CreepJS, pixelscan.net |

A JSON report is saved to `tests/docker_antidetect_report.json` after each run.

---

## Publishing to a registry

```bash
docker tag camouchat-browser-base:latest \
  ghcr.io/camouchat-team/camouchat-browser:0.7.1

docker push ghcr.io/camouchat-team/camouchat-browser:0.7.1
```

Consuming images then reference:

```dockerfile
FROM ghcr.io/camouchat-team/camouchat-browser:0.7.1
```

Tag with the `camouchat-browser` Python package version so the image version
and the library version stay in sync.

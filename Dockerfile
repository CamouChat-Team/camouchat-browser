# camouchat-browser — base Docker image
#
# Provides a ready-to-run Camoufox stealth browser inside a virtual X display.
# Use this as the FROM base for your platform plugin image (e.g. camouchat-whatsapp).
#
# Build:
#   docker build -t camouchat-browser-base:latest .
#
# The Camoufox browser binary is baked into this image at build time so runtime
# containers start instantly without downloading anything.

# ── Stage: base ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    # Anchor ALL XDG dirs under /opt at build time.
    # At runtime the consuming image redirects these to /data (the named volume).
    # Both must agree so Camoufox finds its binary in the same place.
    XDG_CACHE_HOME=/opt/cache \
    XDG_DATA_HOME=/opt/share \
    XDG_STATE_HOME=/opt/state \
    # Signals to CamoufoxBrowser that it is running inside a Docker container.
    # When set to "1", headless mode is forced to "virtual" (Xvfb) for all profiles,
    # overriding any headless=True or headless=False the plugin may pass in.
    CAMOUCHAT_DOCKER=1 \
    # Suppress pip upgrade nags
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ── System dependencies ─────────────────────────────────────────────────────────
# These are the packages a patched Firefox (Camoufox) requires on Debian 13 (trixie),
# taken from Playwright's nativeDeps list adjusted for Debian 13 trixie naming (t64 suffix).
RUN apt-get update && apt-get install -y --no-install-recommends \
    # --- Firefox / Camoufox runtime libs (Debian 13 trixie) ---
    libasound2t64 \
    libatk1.0-0t64 \
    libavcodec61 \
    libcairo-gobject2 \
    libcairo2 \
    libdbus-1-3 \
    libdbus-glib-1-2 \
    libfontconfig1 \
    libfreetype6 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0t64 \
    libgtk-3-0t64 \
    libharfbuzz0b \
    libnss3 \
    libnspr4 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb-shm0 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    # --- Virtual framebuffer (Camoufox headless="virtual" manages Xvfb itself) ---
    xvfb \
    # --- Clipboard (pyperclip requires xclip + a live $DISPLAY) ---
    xclip \
    # --- Fonts (emoji + Latin — prevents blank-page rendering on platform Web apps) ---
    fonts-liberation \
    fonts-noto-color-emoji \
    # --- TLS certs ---
    ca-certificates \
    # --- uv installer dep ---
    curl \
 && rm -rf /var/lib/apt/lists/*

# ── Install uv (fast Python package manager, mirrors CI setup) ─────────────────
RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# ── Install Python packages ────────────────────────────────────────────────────
# Install camouchat-core then camouchat-browser from PyPI.
# For development / local builds you can override with:
#   --build-arg CORE_REF="git+https://github.com/CamouChat-Team/camouchat-core@dev"
ARG CORE_REF="camouchat-core"
ARG BROWSER_REF="camouchat-browser"

RUN uv pip install --system "${CORE_REF}" "${BROWSER_REF}"

# ── Bake the Camoufox browser binary into the image ───────────────────────────
# This fetches the patched Firefox release once at build time.
# XDG_CACHE_HOME=/opt/cache → binary lands at /opt/cache/camoufox
# The runtime image must set XDG_CACHE_HOME to the same path (or to /data/cache).
RUN python -m camoufox fetch

# Firefox writes a profile lock here even in read-only setups — must exist.
# Use /opt/camoufox (not /root/.camoufox) so the non-root app user can reach it.
# /root is mode 700; chown-ing a subdirectory there does not grant traverse access.
RUN mkdir -p /opt/camoufox /opt/cache /opt/share /opt/state
ENV HOME=/home/app

# ── Non-root user ──────────────────────────────────────────────────────────────
# Running as root inside a container is a security risk; create a dedicated user.
# The consuming image should chown /data to this user.
RUN useradd --create-home --shell /bin/bash app \
 && chown -R app:app /opt/camoufox /opt/cache /opt/share /opt/state

USER app
WORKDIR /home/app

# ── Entrypoint ──────────────────────────────────────────────────────────────────
# Copies the Camoufox binary from the image layer to the runtime volume on first
# boot, then hands off to CMD. Plugin images that need their own setup should
# COPY their entrypoint and call this one first:
#   ENTRYPOINT ["/home/app/plugin-entrypoint.sh"]
#   where plugin-entrypoint.sh ends with: exec /home/app/entrypoint.sh "$@"
COPY --chown=app:app entrypoint.sh /home/app/entrypoint.sh
RUN chmod +x /home/app/entrypoint.sh
ENTRYPOINT ["/home/app/entrypoint.sh"]

# ── Labels ──────────────────────────────────────────────────────────────────────
LABEL org.opencontainers.image.title="camouchat-browser" \
      org.opencontainers.image.description="Camoufox stealth browser base image for CamouChat plugins" \
      org.opencontainers.image.source="https://github.com/CamouChat-Team/camouchat-browser"

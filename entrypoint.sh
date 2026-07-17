#!/bin/bash
# camouchat-browser entrypoint
#
# Copies the Camoufox browser binary from the image layer (/opt/cache/camoufox)
# to the runtime XDG cache volume (/data/cache/camoufox) on first boot.
#
# Why: the binary is baked into the image at XDG_CACHE_HOME=/opt/cache (build-time),
# but at runtime the volume sets XDG_CACHE_HOME=/data/cache. Camoufox looks there.
# Without this copy the binary is never found and the browser will not start.
set -euo pipefail

BINARY_SRC="/opt/cache/camoufox"
BINARY_DST="${XDG_CACHE_HOME:-/data/cache}/camoufox"

if [ -d "$BINARY_SRC" ] && [ ! -d "$BINARY_DST" ]; then
    echo "[camouchat] First boot: copying Camoufox binary to volume..."
    mkdir -p "$(dirname "$BINARY_DST")"
    cp -r "$BINARY_SRC" "$BINARY_DST"
    echo "[camouchat] Camoufox binary ready at $BINARY_DST"
fi

exec "$@"

#!/usr/bin/env bash
# YouTube Subscriptions Manager - Linux/macOS Installer
# Usage: curl -fsSL https://github.com/savvy773/app-yt-subs-manager/releases/latest/download/install.sh | bash

set -e

MANIFEST_URL="https://github.com/savvy773/app-yt-subs-manager/releases/latest/download/manifest.json"
APP_NAME="YouTube Subscriptions Manager"

echo "$APP_NAME Installer"

# ── Step 1: Install uv (handles Python automatically, no Python required) ─────
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# ── Step 2: Ensure Python is available (uv manages it internally) ─────────────
echo "Ensuring Python is available..."
uv python install

# ── Step 3: Fetch manifest ────────────────────────────────────────────────────
echo "Fetching manifest..."
manifest=$(curl -fsSL "$MANIFEST_URL")
version=$(echo "$manifest"  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['version'])")
url=$(echo "$manifest"      | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['assets']['wheel']['url'])")
filename=$(echo "$manifest" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['assets']['wheel']['filename'])")
expected=$(echo "$manifest" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['assets']['wheel']['blake3'])")

echo "Version : $version"
echo "File    : $filename"

# ── Step 4: Download wheel ────────────────────────────────────────────────────
tmp_dir=$(mktemp -d)
dest="$tmp_dir/$filename"

echo "Downloading..."
curl -fSL "$url" -o "$dest"

# ── Step 5: Verify blake3 (via uv ephemeral env — no global blake3 needed) ───
echo "Verifying blake3 hash..."
actual=$(uv run --with blake3 --no-project python3 -c "
import blake3, sys
h = blake3.blake3()
with open(sys.argv[1], 'rb') as f:
    for chunk in iter(lambda: f.read(1048576), b''):
        h.update(chunk)
print(h.hexdigest())
" "$dest" 2>/dev/null || echo "")

if [ -z "$actual" ]; then
    echo "WARNING: blake3 verification skipped."
elif [ "$actual" = "$expected" ]; then
    echo "Hash OK: $actual"
else
    echo "Hash MISMATCH! Aborting."
    echo "  Expected: $expected"
    echo "  Got     : $actual"
    rm -rf "$tmp_dir"
    exit 1
fi

# ── Step 6: Install with uv tool ──────────────────────────────────────────────
echo "Installing $filename..."
uv tool install "$dest" --upgrade

# ── Step 7: Install Playwright Chromium ──────────────────────────────────────
echo "Installing Chromium browser..."
uvx playwright install chromium

# ── Cleanup ───────────────────────────────────────────────────────────────────
rm -rf "$tmp_dir"

echo ""
echo "Installation complete! Run with: yt-subs"

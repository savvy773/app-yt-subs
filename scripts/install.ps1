# YouTube Subscriptions Manager - Windows Installer
# Usage: irm https://github.com/savvy773/app-yt-subs-manager/releases/latest/download/install.ps1 | iex

$MANIFEST_URL = "https://github.com/savvy773/app-yt-subs-manager/releases/latest/download/manifest.json"
$APP_NAME     = "YouTube Subscriptions Manager"

Write-Host "$APP_NAME Installer" -ForegroundColor Cyan

# ── Step 1: Install uv (handles Python automatically, no Python required) ────
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..." -ForegroundColor Gray
    irm https://astral.sh/uv/install.ps1 | iex
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
}

# ── Step 2: Ensure Python is available (uv manages it internally) ─────────────
Write-Host "Ensuring Python is available..." -ForegroundColor Gray
uv python install

# ── Step 3: Fetch manifest ────────────────────────────────────────────────────
Write-Host "Fetching manifest..." -ForegroundColor Gray
$manifest = Invoke-RestMethod -Uri $MANIFEST_URL
$version  = $manifest.version
$url      = $manifest.assets.wheel.url
$filename = $manifest.assets.wheel.filename
$expected = $manifest.assets.wheel.blake3

Write-Host "Version : $version"
Write-Host "File    : $filename"

# ── Step 4: Download wheel ────────────────────────────────────────────────────
$tmpDir  = Join-Path $env:TEMP "yt-subs-install"
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
$dest = Join-Path $tmpDir $filename

Write-Host "Downloading..." -ForegroundColor Gray
Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing

# ── Step 5: Verify blake3 (via uv ephemeral env — no global blake3 needed) ───
Write-Host "Verifying blake3 hash..." -ForegroundColor Gray
$verifyScript = @"
import blake3, sys
h = blake3.blake3()
with open(sys.argv[1], 'rb') as f:
    for chunk in iter(lambda: f.read(1048576), b''):
        h.update(chunk)
print(h.hexdigest())
"@
$actual = (uv run --with blake3 --no-project python -c $verifyScript $dest 2>$null)

if (-not $actual) {
    Write-Host "WARNING: blake3 verification skipped." -ForegroundColor Yellow
} elseif ($actual -eq $expected) {
    Write-Host "Hash OK: $actual" -ForegroundColor Green
} else {
    Write-Host "Hash MISMATCH! Aborting." -ForegroundColor Red
    Write-Host "  Expected: $expected"
    Write-Host "  Got     : $actual"
    Remove-Item $dest -Force
    exit 1
}

# ── Step 6: Install with uv tool ──────────────────────────────────────────────
Write-Host "Installing $filename..." -ForegroundColor Gray
uv tool install $dest --upgrade

# ── Step 7: Install Playwright Chromium ──────────────────────────────────────
Write-Host "Installing Chromium browser..." -ForegroundColor Gray
uvx playwright install chromium

# ── Cleanup ───────────────────────────────────────────────────────────────────
Remove-Item $tmpDir -Recurse -Force

Write-Host ""
Write-Host "Installation complete! Run with: yt-subs" -ForegroundColor Cyan

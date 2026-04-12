# YouTube Subscriptions Manager - Windows Installer
# Usage: irm https://github.com/savvy773/app-yt-subs-manager/releases/latest/download/install.ps1 | iex

$ErrorActionPreference = 'Continue'

$MANIFEST_URL = "https://github.com/savvy773/app-yt-subs-manager/releases/latest/download/manifest.json"
$APP_NAME     = "YouTube Subscriptions Manager"
$toolBin      = "$env:USERPROFILE\.local\bin"

Write-Host "$APP_NAME Installer" -ForegroundColor Cyan

# ── Step 1: Install uv (handles Python automatically, no Python required) ────
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..." -ForegroundColor Gray
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:PATH = "$toolBin;$env:PATH"
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

# ── Step 8: Create Desktop Shortcut ──────────────────────────────────────────
Write-Host "Creating desktop shortcut..." -ForegroundColor Gray
$exePath      = "$toolBin\yt-subs.exe"
$iconUrl      = "https://github.com/savvy773/app-yt-subs-manager/releases/latest/download/icon.ico"
$iconPath     = "$toolBin\yt-subs.ico"
$desktopPath  = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "$APP_NAME.lnk"

try {
    Invoke-WebRequest -Uri $iconUrl -OutFile $iconPath -UseBasicParsing -ErrorAction Stop
} catch {
    $iconPath = $exePath
}

$wsh      = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath       = $exePath
$shortcut.WorkingDirectory = $env:USERPROFILE
$shortcut.IconLocation     = "$iconPath,0"
$shortcut.Description      = $APP_NAME
$shortcut.Save()

Write-Host "Desktop shortcut created!" -ForegroundColor Green

# ── Cleanup ───────────────────────────────────────────────────────────────────
Remove-Item $tmpDir -Recurse -Force

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Cyan
Write-Host "  Run with : yt-subs"
Write-Host "  Location : $toolBin\yt-subs.exe"
Write-Host ""
Write-Host "If 'yt-subs' is not found, add the following to your PATH:" -ForegroundColor Yellow
Write-Host "  $toolBin" -ForegroundColor Yellow

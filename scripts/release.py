import subprocess
import sys
import tomllib
from pathlib import Path

# Absolute Project Root
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
PYPROJECT_FILE = PROJECT_ROOT / "pyproject.toml"
DIST_DIR = PROJECT_ROOT / "dist"

def get_current_version():
    try:
        with open(PYPROJECT_FILE, "rb") as f:
            data = tomllib.load(f)
            return data["project"]["version"]
    except Exception: return "1.0.0"

def run_release(title=None, notes=None):
    version = get_current_version()
    tag = f"v{version}"
    print(f"🚀 [Standalone Release] Launching {tag} to GitHub...")
    
    exe_asset = DIST_DIR / f"yt-subs-manager-{tag}.exe"
    zip_asset = DIST_DIR / f"yt-subs-windows-full-{tag}.zip"

    if not exe_asset.exists():
        print(f"⚠️ Warning: EXE asset missing ({exe_asset})")
    
    if not zip_asset.exists():
        print(f"⚠️ Warning: ZIP asset missing ({zip_asset})")

    if not exe_asset.exists() and not zip_asset.exists():
        print(f"❌ Both assets missing! Run 'python scripts/build.py' first.")
        return

    assets = []
    if exe_asset.exists(): assets.append(str(exe_asset))
    if zip_asset.exists(): assets.append(str(zip_asset))

    try:
        # Create Release or overwrite if exists
        print(f"📤 Uploading assets for {tag}...")
        
        cmd = [
            "gh", "release", "create", tag,
            *assets,
            "--title", title if title else f"Release {tag}",
        ]
        if notes:
            cmd.extend(["--notes", notes])
        else:
            cmd.append("--generate-notes")

        subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
        print(f"✅ NEW release {tag} created!")

    except subprocess.CalledProcessError:
        print(f"🔄 Release {tag} already exists. Attempting asset upload...")
        subprocess.run([
            "gh", "release", "upload", tag,
            *assets,
            "--clobber"
        ], check=True, cwd=PROJECT_ROOT)
        print(f"✅ Version {tag} assets updated!")

    subprocess.run(["gh", "browse", "--releases"], cwd=PROJECT_ROOT)

if __name__ == "__main__":
    # Usage: python scripts/release.py "Title" "Notes"
    custom_title = sys.argv[1] if len(sys.argv) > 1 else None
    custom_notes = sys.argv[2] if len(sys.argv) > 2 else None
    run_release(custom_title, custom_notes)


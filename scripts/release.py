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

def run_release():
    version = get_current_version()
    tag = f"v{version}"
    print(f"🚀 [Standalone Release] Launching {tag} to GitHub...")
    
    exe_asset = DIST_DIR / f"yt-subs-manager-{tag}.exe"
    zip_asset = DIST_DIR / f"yt-subs-windows-full-{tag}.zip"

    if not exe_asset.exists() or not zip_asset.exists():
        print(f"❌ Assets missing! Run 'python scripts/build.py' first.")
        return

    try:
        # Create Release or overwrite if exists
        print(f"📤 Uploading assets for {tag}...")
        subprocess.run([
            "gh", "release", "create", tag,
            str(exe_asset), str(zip_asset),
            "--title", f"Release {tag}",
            "--notes", f"Official standalone release {tag}.",
            "--generate-notes"
        ], check=True, capture_output=True, cwd=PROJECT_ROOT)
        print(f"✅ NEW release {tag} created!")

    except subprocess.CalledProcessError:
        print(f"🔄 Release {tag} exists. Overwriting files...")
        subprocess.run([
            "gh", "release", "upload", tag,
            str(exe_asset), str(zip_asset),
            "--clobber"
        ], check=True, cwd=PROJECT_ROOT)
        print(f"✅ Version {tag} assets updated!")

    subprocess.run(["gh", "browse", "--releases"], cwd=PROJECT_ROOT)

if __name__ == "__main__":
    run_release()

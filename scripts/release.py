import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DIST_DIR = PROJECT_ROOT / "dist"

def run_release(version):
    if not version.startswith("v"): version = f"v{version}"
    print(f"🚀 Creating GitHub Release: {version}")
    
    exe_asset = DIST_DIR / f"yt-subs-manager-{version}.exe"
    zip_asset = DIST_DIR / f"yt-subs-windows-full-{version}.zip"

    if not exe_asset.exists() or not zip_asset.exists():
        print(f"❌ Error: Files for {version} not found in 'dist/' folder.")
        print("💡 First run: python scripts/build.py [version]")
        return

    try:
        subprocess.run([
            "gh", "release", "create", version,
            str(exe_asset), str(zip_asset),
            "--title", f"Release {version}",
            "--notes", f"Official high-performance release {version}.",
            "--generate-notes"
        ], check=True, cwd=PROJECT_ROOT)
        print(f"✅ Version {version} is now LIVE!")
        subprocess.run(["gh", "browse", "--releases"], cwd=PROJECT_ROOT)
    except Exception as e:
        print(f"❌ Release failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/release.py [version]")
    else:
        run_release(sys.argv[1])

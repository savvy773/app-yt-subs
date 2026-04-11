import subprocess
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.absolute()
SOURCE_DIR = PROJECT_ROOT / "src" / "yt_subs"
DIST_DIR = PROJECT_ROOT / "dist"

def run_build(version):
    print(f"📦 Starting Build: {version}")
    
    # 1. Clean DIST_DIR only
    if DIST_DIR.exists(): shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    # 2. Flet Build (Run from PROJECT_ROOT to avoid confusion)
    try:
        subprocess.run([
            "flet", "build", "windows", 
            "--main", "src/yt_subs/main.py"
        ], check=True, cwd=PROJECT_ROOT)

        # 3. Locate output
        # Flet build outputs to [PROJECT_ROOT]/build/windows
        BUILD_OUT = PROJECT_ROOT / "build" / "windows"
        exe_list = list(BUILD_OUT.glob("*.exe"))
        
        if exe_list:
            shutil.copy(str(exe_list[0]), str(DIST_DIR / f"yt-subs-manager-{version}.exe"))
            shutil.make_archive(str(DIST_DIR / f"yt-subs-windows-full-{version}"), 'zip', str(BUILD_OUT))
            print(f"✅ Build completed in 'dist/' folder.")
        else:
            print("❌ Build output not found.")
            
    except Exception as e:
        print(f"❌ Build failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/build.py [version]")
    else:
        run_build(sys.argv[1])

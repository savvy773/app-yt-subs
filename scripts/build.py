import subprocess
import shutil
import sys
import tomllib
import os
from pathlib import Path

# Absolute Project Root
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
PYPROJECT_FILE = PROJECT_ROOT / "pyproject.toml"
SOURCE_FILE = PROJECT_ROOT / "src" / "yt_subs" / "main.py"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"

def get_current_version():
    try:
        with open(PYPROJECT_FILE, "rb") as f:
            data = tomllib.load(f)
            return data["project"]["version"]
    except Exception as e:
        print(f"⚠️ Version read error: {e}")
        return "1.0.0"

def clean_temp_files(version):
    print("🧹 Cleaning up build artifacts...")
    if BUILD_DIR.exists(): shutil.rmtree(BUILD_DIR)
    spec_file = PROJECT_ROOT / f"yt-subs-manager-v{version}.spec"
    if spec_file.exists(): os.remove(spec_file)

def run_build():
    version = get_current_version()
    tag = f"v{version}"
    print(f"📦 [Standalone Build] {tag} starting...")
    
    if DIST_DIR.exists(): shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    # Identify python executable (Ensure it's from our .venv)
    # When running via F5 in VS Code, sys.executable should point to the .venv
    python_exe = sys.executable
    print(f"🐍 Using Python: {python_exe}")

    try:
        print(f"🚀 Packing {tag} into standalone EXE...")
        
        # We call flet_cli.cli via python module
        process = subprocess.run([
            python_exe, "-m", "flet_cli.cli", "pack", str(SOURCE_FILE),
            "--name", f"yt-subs-manager-{tag}"
        ], check=True, cwd=PROJECT_ROOT)

        exe_name = f"yt-subs-manager-{tag}.exe"
        exe_file = DIST_DIR / exe_name
        
        if exe_file.exists():
            print(f"🗜️ Creating ZIP package for {tag}...")
            shutil.make_archive(
                str(DIST_DIR / f"yt-subs-windows-full-{tag}"), 
                'zip', 
                root_dir=str(DIST_DIR), 
                base_dir=exe_name
            )
            print(f"\n✅ SUCCESS! Build {tag} is complete.")
            clean_temp_files(version)
        else:
            print(f"❌ Build output missing at: {exe_file}")
            
    except Exception as e:
        print(f"\n❌ Build failed: {e}")

if __name__ == "__main__":
    run_build()

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
    if BUILD_DIR.exists(): 
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
    
    # Clean up any .spec files in the root
    for spec in PROJECT_ROOT.glob("*.spec"):
        try:
            os.remove(spec)
        except: pass

def run_build():
    version = get_current_version()
    tag = f"v{version}"
    # Use a consistent name for the binary
    base_name = f"yt-subs-manager-{tag}"
    
    print(f"📦 [Standalone Build] {tag} starting...")
    
    # Clean dist directory before starting
    if DIST_DIR.exists(): 
        shutil.rmtree(DIST_DIR, ignore_errors=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    
    # Identify python executable from .venv
    venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = Path(sys.executable) # Fallback
    
    print(f"🐍 Using Python: {venv_python}")

    try:
        print(f"🚀 Packing {tag} into standalone EXE...")
        
        # Use flet_cli.cli pack
        # --name sets the output filename in the dist folder
        subprocess.run([
            str(venv_python), "-m", "flet_cli.cli", "pack", str(SOURCE_FILE),
            "--name", base_name
        ], check=True, cwd=PROJECT_ROOT)

        exe_name = f"{base_name}.exe"
        exe_file = DIST_DIR / exe_name
        
        if exe_file.exists():
            print(f"✅ Executable created: {exe_file}")
            
            print(f"🗜️ Creating ZIP package for {tag}...")
            zip_name = f"yt-subs-windows-full-{tag}"
            shutil.make_archive(
                str(DIST_DIR / zip_name), 
                'zip', 
                root_dir=str(DIST_DIR), 
                base_dir=exe_name
            )
            print(f"✅ ZIP created: {DIST_DIR / (zip_name + '.zip')}")
            
            print(f"\n✨ SUCCESS! Build {tag} is complete.")
            clean_temp_files(version)
        else:
            print(f"❌ Build output missing at: {exe_file}")
            # List files in dist to help debug
            if DIST_DIR.exists():
                print(f"Contents of {DIST_DIR}: {[f.name for f in DIST_DIR.iterdir()]}")
            
    except Exception as e:
        print(f"\n❌ Build failed: {e}")

if __name__ == "__main__":
    run_build()

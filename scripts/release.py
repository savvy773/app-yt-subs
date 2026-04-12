"""
Release script: uv build → blake3 hash → manifest.json → gh release upload

Usage:
    python scripts/release.py
    python scripts/release.py "Custom Title" "Release notes here"
"""

import json
import subprocess
import sys
import tomllib
from pathlib import Path

SCRIPTS_DIR  = Path(__file__).parent
PROJECT_ROOT = SCRIPTS_DIR.parent.absolute()
DIST_DIR     = PROJECT_ROOT / "dist"
PYPROJECT    = PROJECT_ROOT / "pyproject.toml"
REPO         = "savvy773/app-yt-subs-manager"


def get_version() -> str:
    with open(PYPROJECT, "rb") as f:
        return tomllib.load(f)["project"]["version"]


def blake3_hash(path: Path) -> str:
    """Run blake3 via uv ephemeral env — no global blake3 needed."""
    script = (
        "import blake3, sys\n"
        "h = blake3.blake3()\n"
        "with open(sys.argv[1], 'rb') as f:\n"
        "    for chunk in iter(lambda: f.read(1048576), b''):\n"
        "        h.update(chunk)\n"
        "print(h.hexdigest())"
    )
    result = subprocess.run(
        ["uv", "run", "--with", "blake3", "--no-project", "python", "-c", script, str(path)],
        capture_output=True, text=True, check=True, cwd=PROJECT_ROOT,
    )
    return result.stdout.strip()


def build_wheel() -> Path:
    print("Building wheel with uv...")
    # Clean old dist
    for f in DIST_DIR.glob("*.whl"):
        f.unlink()
    subprocess.run(["uv", "build", "--wheel"], check=True, cwd=PROJECT_ROOT)
    wheels = list(DIST_DIR.glob("*.whl"))
    if not wheels:
        raise FileNotFoundError("uv build produced no .whl in dist/")
    return wheels[0]


def make_manifest(wheel: Path, tag: str) -> Path:
    base_url = f"https://github.com/{REPO}/releases/download/{tag}"
    print(f"Computing blake3 hash for {wheel.name}...")
    digest = blake3_hash(wheel)
    print(f"  blake3: {digest}")

    manifest = {
        "version": tag.lstrip("v"),
        "assets": {
            "wheel": {
                "url":      f"{base_url}/{wheel.name}",
                "filename": wheel.name,
                "blake3":   digest,
            }
        },
    }
    out = DIST_DIR / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2))
    print(f"manifest.json written → {out}")
    return out


def gh_release(tag: str, assets: list[Path], title: str | None, notes: str | None):
    asset_args = [str(a) for a in assets]

    cmd = [
        "gh", "release", "create", tag,
        *asset_args,
        "--title", title or f"Release {tag}",
        "--repo", REPO,
    ]
    if notes:
        cmd += ["--notes", notes]
    else:
        cmd.append("--generate-notes")

    print(f"\nUploading {len(assets)} assets for {tag}...")
    try:
        subprocess.run(cmd, check=True, cwd=PROJECT_ROOT)
        print(f"✅ Release {tag} created!")
    except subprocess.CalledProcessError:
        # Release already exists — overwrite assets
        print(f"Release {tag} exists. Overwriting assets...")
        subprocess.run(
            ["gh", "release", "upload", tag, *asset_args, "--clobber", "--repo", REPO],
            check=True, cwd=PROJECT_ROOT,
        )
        print(f"✅ {tag} assets updated!")

    subprocess.run(["gh", "browse", "--releases", "--repo", REPO], cwd=PROJECT_ROOT)


def run_release(title: str | None = None, notes: str | None = None):
    version = get_version()
    tag     = f"v{version}"
    print(f"🚀 Releasing {tag}...")

    # 1. Build wheel
    wheel = build_wheel()
    print(f"Wheel: {wheel.name}")

    # 2. Generate manifest.json with blake3
    manifest = make_manifest(wheel, tag)

    # 3. Collect assets
    assets: list[Path] = [wheel, manifest]
    for extra in [
        SCRIPTS_DIR / "install.ps1",
        SCRIPTS_DIR / "install.sh",
        PROJECT_ROOT / "images" / "icon.ico",
    ]:
        if extra.exists():
            assets.append(extra)

    # 4. Upload to GitHub
    gh_release(tag, assets, title, notes)


if __name__ == "__main__":
    custom_title = sys.argv[1] if len(sys.argv) > 1 else None
    custom_notes = sys.argv[2] if len(sys.argv) > 2 else None
    run_release(custom_title, custom_notes)

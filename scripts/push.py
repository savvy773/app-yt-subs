import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Move to project root (D:\Code\Python\yt_subs)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

def run_git_commands(message=None):
    if not message:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Update: {timestamp}"

    try:
        print(f"🚀 Pushing changes to GitHub...")
        subprocess.run(["git", "add", "."], check=True, cwd=PROJECT_ROOT)
        subprocess.run(["git", "commit", "-m", message], check=True, cwd=PROJECT_ROOT)
        subprocess.run(["git", "push", "origin", "main"], check=True, cwd=PROJECT_ROOT)
        print("\n✅ Successfully pushed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else None
    run_git_commands(msg)

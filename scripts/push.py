import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Absolute Project Root (One level up from this script)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

def run_sync_push(custom_message=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"{custom_message} ({timestamp})" if custom_message else f"sync to server - {timestamp}"

    try:
        print(f"🚀 [Standalone] Syncing to GitHub...")
        # Remove all tracked files from index, then re-add respecting .gitignore
        # This ensures files newly added to .gitignore are deleted from remote
        subprocess.run(["git", "rm", "-r", "--cached", "."], check=True, cwd=PROJECT_ROOT)
        subprocess.run(["git", "add", "-A"], check=True, cwd=PROJECT_ROOT)
        
        try:
            subprocess.run(["git", "commit", "-m", commit_msg], check=True, cwd=PROJECT_ROOT)
        except subprocess.CalledProcessError:
            print("ℹ️ No changes to commit.")

        print("📤 Pushing to origin main...")
        # Use simple push, if they want forced they can add -f
        subprocess.run(["git", "push", "origin", "main"], check=True, cwd=PROJECT_ROOT)
        print("\n✅ STANDALONE SYNC COMPLETE!")
    except Exception as e:
        print(f"\n❌ Sync failed: {e}")

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else None
    run_sync_push(msg)

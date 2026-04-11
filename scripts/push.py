import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Project Root (D:\Code\Python\yt_subs)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

def run_sync_push(custom_message=None):
    # 1. Create automatic message with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if custom_message:
        commit_msg = f"{custom_message} ({timestamp})"
    else:
        # Default message as requested
        commit_msg = f"sync to server, all files from project - {timestamp}"

    try:
        print(f"🚀 Starting forced sync to GitHub...")
        print(f"📝 Message: {commit_msg}")
        
        # Step 1: git add .
        subprocess.run(["git", "add", "."], check=True, cwd=PROJECT_ROOT)

        # Step 2: git commit -m "..."
        # If there are no changes, commit might fail, so we handle it.
        try:
            subprocess.run(["git", "commit", "-m", commit_msg], check=True, cwd=PROJECT_ROOT)
        except subprocess.CalledProcessError:
            print("ℹ️ No changes to commit.")

        # Step 3: git push -f origin main
        print("📤 Pushing forcefully (-f) to origin main...")
        subprocess.run(["git", "push", "-f", "origin", "main"], check=True, cwd=PROJECT_ROOT)

        print("\n✅ Sync complete! GitHub is now identical to your local project.")
        
    except Exception as e:
        print(f"\n❌ Sync failed: {e}")

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else None
    run_sync_push(msg)

import subprocess
import sys
from datetime import datetime

def run_git_commands(message=None):
    # Set default commit message if none provided
    if not message:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Update: {timestamp}"

    try:
        print(f"🚀 Starting Git push process...")
        
        # 1. git add .
        print("📦 Staging changes...")
        subprocess.run(["git", "add", "."], check=True)

        # 2. git commit -m "message"
        print(f"✍️ Committing with message: '{message}'")
        subprocess.run(["git", "commit", "-m", message], check=True)

        # 3. git push origin main
        print("📤 Pushing to GitHub (origin main)...")
        subprocess.run(["git", "push", "origin", "main"], check=True)

        print("\n✅ Successfully pushed to GitHub!")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error occurred during Git operation: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    # Check if a custom commit message was provided via command line
    custom_message = sys.argv[1] if len(sys.argv) > 1 else None
    run_git_commands(custom_message)

"""
GameDev Journey - One-Command GitHub Push Script
Uses Dulwich (pure-Python Git) with a GitHub Personal Access Token.
"""

import sys
import os
import dulwich.repo
from dulwich.porcelain import push, add, commit

def main():
    repo_path = os.path.dirname(os.path.abspath(__file__))
    
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[1].strip()
    else:
        print("=" * 60)
        print("  GAMEDEV JOURNEY -> GITHUB PUSH TOOL")
        print("=" * 60)
        print("\nGitHub requires a Personal Access Token (PAT) to push code.")
        print("If you don't have one, get it in 30 seconds:")
        print("1. Go to: https://github.com/settings/tokens")
        print("2. Click 'Generate new token (classic)'")
        print("3. Check 'repo' scope and click 'Generate token'")
        print("4. Copy your token (starts with ghp_...)\n")
        try:
            token = input("Enter your GitHub Personal Access Token: ").strip()
        except EOFError:
            pass

    if not token:
        print("\nError: No token provided. Push cancelled.")
        return

    # Add & commit any unstaged changes
    add(repo_path)
    try:
        commit(repo_path, message=b"Update GameDev Journey web application", author=b"kubendkubend2-star <developer@gamedev.com>")
    except Exception:
        pass # Nothing new to commit

    # Authenticated remote URL
    # https://<TOKEN>@github.com/kubendkubend2-star/gameprotfolio.git
    remote_url = f"https://{token}@github.com/kubendkubend2-star/gameprotfolio.git"

    print(f"\nPushing code to https://github.com/kubendkubend2-star/gameprotfolio ...")
    try:
        push(repo_path, remote_url, refspecs=["refs/heads/master:refs/heads/main"], force=True)
        print("\nSUCCESS! Successfully pushed to branch 'main' on GitHub!")
        print("Render.com will now automatically detect the new commit, find requirements.txt, and build your site!")
    except Exception as e:
        # Fallback refspec attempt
        try:
            push(repo_path, remote_url, refspecs=["HEAD:refs/heads/main"], force=True)
            print("\nSUCCESS! Successfully pushed to branch 'main' on GitHub!")
            print("Render.com will now automatically detect the new commit, find requirements.txt, and build your site!")
        except Exception as e2:
            print(f"\nPush failed: {e2}")
            print("Please check that your token has 'repo' permissions.")

if __name__ == '__main__':
    main()

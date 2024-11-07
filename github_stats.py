import os
import sys
import argparse
from asyncio import run
from datetime import datetime, timezone
from shutil import rmtree

# Set up argument parser
parser = argparse.ArgumentParser(description='Generate GitHub statistics for a user')
parser.add_argument('username', type=str, help='GitHub username to analyze')
args = parser.parse_args()

# Environment setup
os.environ["DEBUG_RUN"] = "True"
os.environ["INPUT_DEBUG_LOGGING"] = "True"
os.environ["INPUT_IGNORED_REPOS"] = ""
os.environ["INPUT_SYMBOL_VERSION"] = "1"
os.environ["INPUT_INCLUDE_ALL_COMMITS"] = "true"  # Include all commits
os.environ["INPUT_REQUEST_PRIVATE"] = "true"      # Include private repos
os.environ["INPUT_INCLUDE_ORG"] = "true"         # Include organization repos

# Read GitHub token from environment or prompt user
if "INPUT_GH_TOKEN" not in os.environ:
    token = input("Please enter your GitHub token: ")
    os.environ["INPUT_GH_TOKEN"] = token

async def run_local():
    try:
        print("Starting local GitHub stats generation...")
        
        # Initialize managers
        from sources.manager_debug import init_debug_manager
        from sources.manager_github import init_github_manager, GitHubManager as GHM
        from sources.manager_file import init_localization_manager
        from sources.manager_download import DownloadManager as DM
        
        # Initialize in correct order
        init_debug_manager()
        init_github_manager()
        
        github_username = args.username  # Get username from command line arguments
        print(f"\nGenerating stats for user: {github_username}")
        
        # Validate if user exists before proceeding
        if not await GHM.user_exists(github_username):
            print(f"Error: GitHub user '{github_username}' does not exist")
            return
        
        await DM.init(github_username)
        init_localization_manager()
        
        # Get stats using the main get_stats function
        from sources.main import get_stats
        stats = await get_stats()
        
        print("\nGenerated Statistics:")
        print("=" * 50)
        print(stats)
        print("=" * 50)
        
        # Clean up
        await DM.close_remote_resources()
        
        # Delete the repo folder
        if os.path.exists("repo"):
            rmtree("repo")
            print("\nCleanup: Removed temporary repository folder")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        # Ensure cleanup happens even if there's an error
        if os.path.exists("repo"):
            rmtree("repo")

if __name__ == "__main__":
    start_time = datetime.now(timezone.utc)
    run(run_local())
    end_time = datetime.now(timezone.utc)
    print(f"\nScript completed in: {end_time - start_time}")

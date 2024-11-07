import os
import sys
from asyncio import run
from datetime import datetime, timezone

from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv()

# Set DEBUG_RUN to True for local testing
os.environ["DEBUG_RUN"] = "True"
os.environ["INPUT_DEBUG_LOGGING"] = "True"

# Add this near the top where other environment variables are set
os.environ["INPUT_IGNORED_REPOS"] = ""  # or a comma-separated list of repos to ignore
os.environ["INPUT_SYMBOL_VERSION"] = "1"  # or "2" or "3" depending on which style you want

# Make sure we have a GitHub token
if "INPUT_GH_TOKEN" not in os.environ:
    print("ERROR: Please set INPUT_GH_TOKEN in your .env file")
    print("You can get a token from: https://github.com/settings/tokens")
    print("Required scopes: repo, user")
    sys.exit(1)

async def run_local():
    print("Starting local GitHub stats generation...")
    
    # Initialize managers
    from sources.manager_debug import init_debug_manager
    from sources.manager_github import init_github_manager, GitHubManager as GHM
    from sources.manager_file import init_localization_manager
    from sources.manager_download import DownloadManager as DM
    
    # Initialize in correct order
    init_debug_manager()
    init_github_manager()
    
    github_username = "AnjaliML"  # Change this to test different users
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

if __name__ == "__main__":
    start_time = datetime.now(timezone.utc)
    run(run_local())
    end_time = datetime.now(timezone.utc)
    print(f"\nScript completed in: {end_time - start_time}")

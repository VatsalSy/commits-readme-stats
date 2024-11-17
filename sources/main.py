"""
GitHub Commit Statistics Generator
"""
from asyncio import run
from datetime import datetime
import os

from sources.manager_download import DownloadManager as DM
from sources.manager_environment import EnvironmentManager as EM
from sources.manager_github import init_github_manager, GitHubManager as GHM
from sources.manager_file import init_localization_manager, FileManager as FM
from sources.manager_debug import init_debug_manager, DebugManager as DBM
from sources.yearly_commit_calculator import calculate_commit_data
from sources.graphics_list_formatter import make_commit_day_time_list
from sources.manager_token import get_token_user, TokenManager
import sys

async def collect_user_repositories(username: str):
    """
    Collects all repositories user has access to.
    """
    DBM.i("Collecting user repositories...")
    repositories = await DM.get_remote_graphql("user_repository_list", username=username)
    DBM.g("User repositories collected!")
    return repositories


async def get_stats() -> str:
    """
    Creates new README.md content with commit statistics.
    """
    DBM.i("Starting stats collection...")
    start_time = datetime.now()

    stats = str()
    repositories = await collect_user_repositories(DM.target_username)

    if EM.SHOW_COMMIT or EM.SHOW_DAYS_OF_WEEK:
        yearly_data, commit_data = await calculate_commit_data(repositories, DM.target_username)
        timezone = "UTC"  # Default to UTC since we don't need WakaTime for timezone
        DBM.i("Adding user commit day time info...")
        stats += f"{await make_commit_day_time_list(timezone, repositories, commit_data)}\n\n"

    DBM.i(f"Repository stats collection completed in {datetime.now() - start_time}")
    DBM.g("Stats for README collected!")
    
    return stats


async def main():
    """
    Application main function.
    Initializes managers, collects commit info and updates README.md.
    """
    # Initialize debug manager first
    init_debug_manager()
    DBM.i("Debug manager initialized.")
    
    # Initialize environment manager
    EM.init()
    DBM.i("Environment manager initialized.")
    
    # Then initialize other managers
    init_github_manager()
    DBM.i("GitHub manager initialized.")
    
    # Initialize with username from environment or GitHub Action input
    username = EM.USERNAME or GHM.USER.login
    await DM.init(username)
    DBM.i("Download manager initialized.")
    
    init_localization_manager()
    DBM.i("Localization manager initialized.")

    # Get the repository owner from GitHub context
    repo_owner = os.getenv('GITHUB_REPOSITORY_OWNER')
    
    # Get token owner
    token_username = get_token_user(TokenManager.get_token())
    
    if repo_owner and token_username and repo_owner.lower() != token_username.lower():
        print(f"Error: Username mismatch - Cannot proceed with repository updates in non-debug mode")
        print(f"Please either:")
        print(f"1. Use the token owner's username")
        print(f"2. Run in debug mode with --debug flag")
        print(f"3. Use a token that belongs to the specified username")
        sys.exit(1)

    stats = await get_stats()
    if not EM.DEBUG_RUN:
        GHM.update_readme(stats)
        GHM.commit_update()
    else:
        DBM.i("\nGenerated Statistics:")
        DBM.i("=" * 50)
        print(stats)
        DBM.i("=" * 50)
        
    await DM.close_remote_resources()


if __name__ == "__main__":
    start_time = datetime.now()
    run(main())
    end_time = datetime.now()
    print(f"Program finished in {end_time - start_time}")

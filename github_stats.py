import os
import sys
from time import time
from shutil import rmtree
from dotenv import load_dotenv
from asyncio import run
from git.exc import GitCommandError
import argparse
import requests

# CRITICAL: Load .env file BEFORE importing any modules that use environment variables
load_dotenv()

from sources.manager_debug import DebugManager as DBM
from sources.manager_token import get_token_user

# Initialize debug logger first
DBM.create_logger()

async def run_local():
    """Run the stats generator locally"""
    try:
        print("Starting local GitHub stats generation...")
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='GitHub Stats Generator')
        parser.add_argument('username', help='GitHub username')
        parser.add_argument('--debug', action='store_true', help='Run in debug mode')
        args = parser.parse_args()
        
        # Use Configuration class for secure settings management
        from sources.manager_config import Configuration
        config = Configuration()
        config.debug = args.debug
        config.username = args.username
        
        # Use TokenManager to get the token consistently
        from sources.manager_token import TokenManager
        token = TokenManager.get_token()  # This will use INPUT_GH_COMMIT_TOKEN
        
        allowPush = True
        if token:
            token_username = get_token_user(token)
            print(f"Debug: Token username: {token_username}")
            if token_username and token_username.lower() != args.username.lower():
                print(f"\nWARNING: The provided username '{args.username}' does not match the token owner '{token_username}'")
                print("This may result in incorrect statistics being generated!\n")
                allowPush = False
        else:
            print("Debug: No GitHub token found")
        
        # Initialize environment first with debug setting
        from sources.manager_environment import EnvironmentManager as EM
        EM.DEBUG_RUN = config.debug
        
        # Apply remaining configuration to environment securely
        for key, value in config.to_env_dict().items():
            if key != "DEBUG_RUN":  # Skip debug since we already set it
                os.environ[key] = value
        
        # Initialize managers
        from sources.manager_debug import DebugManager as DBM, init_debug_manager
        from sources.manager_github import init_github_manager, GitHubManager as GHM
        from sources.manager_file import init_localization_manager
        from sources.manager_download import DownloadManager as DM
        from sources.manager_environment import EnvironmentManager as EM
        
        # Initialize in correct order
        init_debug_manager()
        DBM.i("Debug manager initialized")
        
        # Initialize environment first
        EM.init()
        DBM.i("Environment manager initialized")
        
        init_github_manager()
        DBM.i("GitHub manager initialized")
        
        await DM.init(args.username)
        DBM.i("Download manager initialized")
        
        init_localization_manager()
        DBM.i("Localization manager initialized")
        
        # Get stats using the main get_stats function
        from sources.main import get_stats, get_wakatime_stats
        commit_stats = await get_stats()
        wakatime_stats = await get_wakatime_stats()

        # If not in debug mode, commit and push changes
        if not EM.DEBUG_RUN:
            try:
                if allowPush:
                    # Update README with commit stats
                    GHM.update_readme(commit_stats)

                    # Update README with WakaTime stats if available
                    if wakatime_stats:
                        GHM.update_readme(wakatime_stats, section_name="wakatime")

                    # Commit and push changes
                    GHM.commit_update()
                    print("Changes committed and pushed")
                else:
                    print("Skipping commit and push as username mismatch")
            except Exception as e:
                print(f"Error updating repository: {str(e)}")
                raise
        else:
            DBM.i("\nGenerated Commit Statistics:")
            DBM.i("=" * 50)
            print(commit_stats)
            DBM.i("=" * 50)

            if wakatime_stats:
                DBM.i("\nGenerated WakaTime Statistics:")
                DBM.i("=" * 50)
                print(wakatime_stats)
                DBM.i("=" * 50)
        
    except GitCommandError as e:
        error_msg = DBM.handle_error(
            e,
            context="GitHub operation failed",
            mask_token=True
        )
        print(f"Error: {error_msg}")
        
    except Exception as e:
        error_msg = DBM.handle_error(
            e,
            context="Stats generation failed",
            mask_token=True
        )
        print(f"Error: {error_msg}")
        
    finally:
        # Ensure cleanup happens
        from sources.manager_download import DownloadManager as DM
        await DM.close_remote_resources()
        if os.path.exists("repo"):
            rmtree("repo")

if __name__ == "__main__":
    start_time = time()
    run(run_local())
    print(f"\nScript completed in: {time() - start_time:.6f}")

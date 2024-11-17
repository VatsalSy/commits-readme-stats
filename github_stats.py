import os
import sys
from time import time
from shutil import rmtree
from dotenv import load_dotenv
from asyncio import run
from git.exc import GitCommandError
import argparse
import requests

from sources.manager_debug import DebugManager as DBM

# Initialize debug logger first
DBM.create_logger()

def get_token_user(token):
    """Get the username of the token owner"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v4.idl'
    }
    query = """
    query { 
        viewer { 
            login
        }
    }
    """
    try:
        response = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
        print(f"Debug: API Response status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'viewer' in data['data'] and 'login' in data['data']['viewer']:
                return data['data']['viewer']['login']
            else:
                print(f"Debug: Unexpected response structure: {data}")
        else:
            print(f"Debug: API request failed with status {response.status_code}")
            print(f"Debug: Response content: {response.text}")
    except Exception as e:
        print(f"Debug: Error in get_token_user: {str(e)}")
    return None

async def run_local():
    """Run the stats generator locally"""
    try:
        print("Starting local GitHub stats generation...")
        
        # Load environment variables securely
        load_dotenv()
        
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
        
        if token:
            # print(f"Debug: Found GitHub token")
            token_username = get_token_user(token)
            print(f"Debug: Token username: {token_username}")
            if token_username and token_username.lower() != args.username.lower():
                print(f"\nWARNING: The provided username '{args.username}' does not match the token owner '{token_username}'")
                print("This may result in incorrect statistics being generated!\n")
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
        from sources.main import get_stats
        stats = await get_stats()
        
        # If not in debug mode, commit and push changes
        if not EM.DEBUG_RUN:
            try:
                # Update README with stats
                GHM.update_readme(stats)
                # Commit and push changes
                GHM.commit_update()
                DBM.i("Changes committed and pushed")
            except Exception as e:
                DBM.p(f"Error updating repository: {str(e)}")
                raise
        else:
            DBM.i("\nGenerated Statistics:")
            DBM.i("=" * 50)
            print(stats)
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
        if os.path.exists("repo"):
            rmtree("repo")

if __name__ == "__main__":
    start_time = time()
    run(run_local())
    print(f"\nScript completed in: {time() - start_time:.6f}")

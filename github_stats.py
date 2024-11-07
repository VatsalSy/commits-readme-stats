import os
import sys
from time import time
from shutil import rmtree
from dotenv import load_dotenv
from asyncio import run
from git.exc import GitCommandError

from sources.manager_debug import DebugManager as DBM

async def run_local():
    """Run the stats generator locally"""
    try:
        print("Starting local GitHub stats generation...")
        
        # Load environment variables
        load_dotenv()
        os.environ["DEBUG_RUN"] = "True"
        
        # Get username from command line args
        if len(sys.argv) != 2:
            print("Usage: python github_stats.py <username>")
            return
            
        username = sys.argv[1]
        os.environ["INPUT_USERNAME"] = username
        
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
        
        await DM.init(username)
        DBM.i("Download manager initialized")
        
        init_localization_manager()
        DBM.i("Localization manager initialized")
        
        # Get stats using the main get_stats function
        from sources.main import get_stats
        stats = await get_stats()
        
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

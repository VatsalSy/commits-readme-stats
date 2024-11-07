from asyncio import sleep
from json import dumps
from re import search
from datetime import datetime, timedelta
from typing import Dict, Tuple, List
import os

from .manager_download import DownloadManager as DM
from .manager_environment import EnvironmentManager as EM
from .manager_github import GitHubManager as GHM
from .manager_file import FileManager as FM
from .manager_debug import DebugManager as DBM


async def calculate_commit_data(repositories: List[Dict], target_username: str) -> Tuple[Dict, Dict]:
    """
    Calculate commit data by years.
    Commit data includes contribution additions and deletions in each quarter of each recorded year.

    :param repositories: user repositories info dictionary.
    :param target_username: GitHub username of the authenticated user.
    :returns: Commit quarter yearly data dictionary.
    """
    DBM.i("Calculating commit data...")
    
    # Create cache filename with username
    cache_filename = f"commits_data_{target_username}.pick"
    cache_path = os.path.join("assets", cache_filename)
    
    # Check if cache exists and is recent (less than 4 hours old)
    use_cache = False
    if os.path.exists(cache_path):
        file_modified_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        time_difference = datetime.now() - file_modified_time
        use_cache = time_difference < timedelta(hours=4)
        
        if use_cache:
            DBM.i(f"Using cached data from {file_modified_time}")
        else:
            DBM.i(f"Cache exists but is too old ({time_difference.total_seconds()/3600:.1f} hours)")
    
    # Try to load cached data if it's recent enough
    if use_cache:
        cached_data = FM.cache_binary(cache_filename, assets=True)
        if cached_data is not None:
            DBM.i("Commit data restored from cache!")
            return cached_data[0], cached_data[1]
    
    DBM.i("Fetching fresh commit data...")
    yearly_data = dict()
    date_data = dict()
    
    # Process repositories one by one
    for i, repo in enumerate(repositories, 1):
        DBM.i(f"\t{i}/{len(repositories)} Retrieving repo: {repo['owner']['login']}/{repo['name']}")
        await update_data_with_commit_stats(repo, yearly_data, date_data, target_username)
    
    DBM.i("Commit data calculated!")
    
    # Cache the data for this specific username
    FM.cache_binary(cache_filename, [yearly_data, date_data], assets=True)
    DBM.i("New commit data saved to cache!")
    
    return yearly_data, date_data


async def update_data_with_commit_stats(repo_details: Dict, yearly_data: Dict, date_data: Dict, target_username: str):
    """
    Updates yearly commit data with commits from given repository.
    Skips update if the commit isn't related to any repository.

    :param repo_details: Dictionary with information about the given repository.
    :param yearly_data: Yearly data dictionary to update.
    :param date_data: Commit date dictionary to update.
    :param target_username: GitHub username of the authenticated user.
    """
    try:
        branches_data = await DM.get_remote_graphql(
            "repo_branch_list",
            owner=repo_details["owner"]["login"],
            name=repo_details["name"]
        )
        
        # Extract branch names from the response structure
        branches = [branch["name"] for branch in branches_data["repository"]["refs"]["nodes"]]
        
        for branch_name in branches:
            try:
                commits = await DM.get_remote_graphql(
                    "repo_commit_list",
                    owner=repo_details["owner"]["login"],
                    name=repo_details["name"],
                    branch=branch_name
                )
                
                # Get the commit history nodes
                user_commits = [
                    commit for commit in commits["repository"]["ref"]["target"]["history"]["nodes"]
                    if commit["author"]["user"] and commit["author"]["user"]["login"] == target_username
                ]
                
                for commit in user_commits:
                    date = search(r"\d+-\d+-\d+", commit["committedDate"]).group()
                    curr_year = datetime.fromisoformat(date).year
                    quarter = (datetime.fromisoformat(date).month - 1) // 3 + 1

                    if repo_details["name"] not in date_data:
                        date_data[repo_details["name"]] = dict()
                    if branch_name not in date_data[repo_details["name"]]:
                        date_data[repo_details["name"]][branch_name] = dict()
                    date_data[repo_details["name"]][branch_name][commit["oid"]] = commit["committedDate"]

                    if repo_details["primaryLanguage"] is not None:
                        if curr_year not in yearly_data:
                            yearly_data[curr_year] = dict()
                        if quarter not in yearly_data[curr_year]:
                            yearly_data[curr_year][quarter] = dict()
                        if repo_details["primaryLanguage"]["name"] not in yearly_data[curr_year][quarter]:
                            yearly_data[curr_year][quarter][repo_details["primaryLanguage"]["name"]] = {"add": 0, "del": 0}
                        yearly_data[curr_year][quarter][repo_details["primaryLanguage"]["name"]]["add"] += commit["additions"]
                        yearly_data[curr_year][quarter][repo_details["primaryLanguage"]["name"]]["del"] += commit["deletions"]
                        
            except Exception as e:
                DBM.w(f"\t\tError processing branch {branch_name}: {str(e)}")
                
    except Exception as e:
        DBM.w(f"\t\tError processing repository {repo_details['name']}: {str(e)}")

    if not EM.DEBUG_RUN:
        await sleep(0.4)

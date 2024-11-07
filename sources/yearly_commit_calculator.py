from asyncio import sleep
from json import dumps
from re import search
from datetime import datetime
from typing import Dict, Tuple, List

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
    
    # Try to load cached data for this specific username
    cached_data = FM.cache_binary(cache_filename, assets=True)
    if cached_data is not None:
        DBM.i("Commit data restored from cache!")
        return cached_data[0], cached_data[1]
    
    DBM.i("No cached commit data found for this user, recalculating...")
    yearly_data = dict()
    date_data = dict()
    
    # Process repositories one by one
    for i, repo in enumerate(repositories, 1):
        DBM.i(f"\t{i}/{len(repositories)} Retrieving repo: {repo['owner']['login']}/{repo['name']}")
        await update_data_with_commit_stats(repo, yearly_data, date_data, target_username)
    
    DBM.i("Commit data calculated!")
    
    # Cache the data for this specific username
    FM.cache_binary(cache_filename, [yearly_data, date_data], assets=True)
    DBM.i("Commit data saved to cache!")
    
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
    owner = repo_details["owner"]["login"]
    branch_data = await DM.get_remote_graphql("repo_branch_list", owner=owner, name=repo_details["name"])
    if len(branch_data) == 0:
        DBM.w("\t\tSkipping repo.")
        return

    for branch in branch_data:
        try:
            commit_data = await DM.get_remote_graphql(
                "repo_commit_list", 
                owner=owner, 
                name=repo_details["name"], 
                branch=branch["name"]
            )
            
            # Get the commit history nodes
            commits = commit_data.get("repository", {}).get("ref", {}).get("target", {}).get("history", {}).get("nodes", [])
            
            # More robust filtering of commits
            user_commits = []
            for commit in commits:
                if commit is None:
                    continue
                    
                author = commit.get("author", {})
                if author is None:
                    continue
                    
                user = author.get("user")
                if user is None:
                    continue
                    
                if user.get("login") == target_username:
                    user_commits.append(commit)
            
            for commit in user_commits:
                date = search(r"\d+-\d+-\d+", commit["committedDate"]).group()
                curr_year = datetime.fromisoformat(date).year
                quarter = (datetime.fromisoformat(date).month - 1) // 3 + 1

                if repo_details["name"] not in date_data:
                    date_data[repo_details["name"]] = dict()
                if branch["name"] not in date_data[repo_details["name"]]:
                    date_data[repo_details["name"]][branch["name"]] = dict()
                date_data[repo_details["name"]][branch["name"]][commit["oid"]] = commit["committedDate"]

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
            DBM.w(f"\t\tError processing branch {branch['name']}: {str(e)}")
            continue

        if not EM.DEBUG_RUN:
            await sleep(0.4)

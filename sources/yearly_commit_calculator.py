from asyncio import sleep
from datetime import datetime, timezone
from typing import Dict, Tuple, List, Set
import os
from hashlib import sha256

from .manager_download import DownloadManager as DM, GraphQLHTTPError
from .manager_environment import EnvironmentManager as EM
from .manager_file import FileManager as FM
from .manager_debug import DebugManager as DBM

COMMIT_CACHE_MAX_AGE_SECONDS = 36 * 60 * 60
CACHE_SCHEMA_VERSION = 4


def ensure_cache_dir():
    cache_dir = os.path.join(os.getcwd(), "assets")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


async def calculate_commit_data(
    repositories: List[Dict],
    target_username: str,
) -> Tuple[Dict, Dict, datetime]:
    """
    Calculate authored commit timestamps with secure local caching.

    :param repositories: user repositories info dictionary.
    :param target_username: GitHub username of the authenticated user.
    :returns: Yearly data, commit timestamps, and successful crawl completion time.
    """
    DBM.i("Calculating commit data...")
    cache_enabled = os.getenv("GITHUB_ACTIONS", "").lower() != "true"
    if cache_enabled:
        ensure_cache_dir()
    
    # Create cache filename with username (using hash for safety)
    cache_filename = (
        f"commits_v{CACHE_SCHEMA_VERSION}_"
        f"{sha256(target_username.encode()).hexdigest()}.json"
    )
    
    # GitHub-hosted runners are ephemeral. Avoid producing a cache that cannot
    # be reused, and never upload private-history metadata to a public cache.
    if cache_enabled:
        try:
            cached_data = FM.cache_binary(
                cache_filename,
                assets=True,
                max_age_seconds=COMMIT_CACHE_MAX_AGE_SECONDS,
            )
            if cached_data is not None:
                yearly_data, date_data, completed_at_value = cached_data
                
                # Validate cache structure without using string operations
                if (isinstance(yearly_data, dict) and
                    isinstance(date_data, dict) and
                    isinstance(completed_at_value, str) and
                    all(isinstance(v, dict) for v in yearly_data.values()) and
                    all(isinstance(v, dict) for v in date_data.values())):

                    completed_at = datetime.fromisoformat(completed_at_value)
                    if completed_at.tzinfo is None:
                        raise ValueError("Cached crawl completion time has no timezone")
                    DBM.i("Commit data restored from cache!")
                    return yearly_data, date_data, completed_at
                else:
                    DBM.w("Cache data validation failed - fetching fresh data")
        except Exception as e:
            DBM.w(f"Cache load failed: {str(e)} - fetching fresh data")
    else:
        DBM.i("Skipping commit cache on the GitHub-hosted runner.")

    DBM.i("Fetching fresh commit data...")
    yearly_data = dict()
    date_data = dict()
    seen_commit_oids: Set[str] = set()

    identity = await DM.get_remote_graphql("user_identity", username=target_username)
    author_id = identity["user"]["id"]
    account_created_year = datetime.fromisoformat(
        identity["user"]["createdAt"].replace("Z", "+00:00")
    ).year
    
    # Process repositories one by one
    for i, repo in enumerate(repositories, 1):
        DBM.i(f"\t{i}/{len(repositories)} Retrieving repo: {repo['owner']['login']}/{repo['name']}")
        await update_data_with_commit_stats(
            repo,
            yearly_data,
            date_data,
            target_username,
            author_id,
            seen_commit_oids,
            account_created_year,
        )
    
    DBM.i("Commit data calculated!")
    completed_at = datetime.now(timezone.utc)
    
    if cache_enabled:
        # Cache the data for this specific username during local development.
        FM.cache_binary(
            cache_filename,
            [yearly_data, date_data, completed_at.isoformat()],
            assets=True,
        )
        DBM.i("New commit data saved to cache!")
    
    return yearly_data, date_data, completed_at


def repository_key(repo_details: Dict) -> str:
    """Return a collision-safe repository identifier."""
    return repo_details.get(
        "nameWithOwner",
        f"{repo_details['owner']['login']}/{repo_details['name']}",
    )


async def get_default_branch_commits(
    repo_details: Dict,
    branch_name: str,
    author_id: str,
    account_created_year: int,
) -> List[Dict]:
    """Fetch one default-branch history, partitioning only persistent 5xx cases."""
    query_args = {
        "owner": repo_details["owner"]["login"],
        "name": repo_details["name"],
        "branch": branch_name,
        "authorId": author_id,
    }
    try:
        commits = await DM.get_remote_graphql("repo_commit_list", **query_args)
        return commits["repository"]["ref"]["target"]["history"]["nodes"]
    except GraphQLHTTPError as error:
        if error.status_code not in (502, 503, 504):
            raise

    DBM.w(
        "\t\tFull history query failed after retries; "
        "retrying in bounded yearly windows."
    )
    commit_nodes = []
    for year in range(account_created_year, datetime.now().year + 1):
        commits = await DM.get_remote_graphql(
            "repo_commit_list_window",
            **query_args,
            since=f"{year}-01-01T00:00:00Z",
            until=f"{year + 1}-01-01T00:00:00Z",
        )
        commit_nodes.extend(
            commits["repository"]["ref"]["target"]["history"]["nodes"]
        )
    return commit_nodes


async def update_data_with_commit_stats(
    repo_details: Dict,
    yearly_data: Dict,
    date_data: Dict,
    target_username: str,
    author_id: str,
    seen_commit_oids: Set[str],
    account_created_year: int,
):
    """
    Updates yearly commit data with commits from given repository.
    Skips update if the commit isn't related to any repository.

    :param repo_details: Dictionary with information about the given repository.
    :param yearly_data: Yearly data dictionary to update.
    :param date_data: Commit date dictionary to update.
    :param target_username: GitHub username of the authenticated user.
    """
    repo_key = repository_key(repo_details)
    default_branch = repo_details.get("defaultBranchRef")
    branch_name = default_branch.get("name") if default_branch else None
    if not branch_name:
        DBM.i(f"\t\t{repo_key}: skipped empty repository")
        return

    repo_commit_count = 0

    try:
        commits = await get_default_branch_commits(
            repo_details,
            branch_name,
            author_id,
            account_created_year,
        )

        # Get the commit history nodes
        user_commits = [
            commit for commit in commits
            if commit.get("author")
            and commit["author"].get("user")
            and commit["author"]["user"]["login"].lower() == target_username.lower()
            and commit["oid"] not in seen_commit_oids
        ]

        # Deduplicate Git objects across repositories and forks.
        for commit in user_commits:
            seen_commit_oids.add(commit["oid"])
            repo_commit_count += 1
            
            if repo_key not in date_data:
                date_data[repo_key] = dict()
            if branch_name not in date_data[repo_key]:
                date_data[repo_key][branch_name] = dict()
            date_data[repo_key][branch_name][commit["oid"]] = commit["committedDate"]
                
    except Exception as e:
        DBM.w(f"\t\tError processing default branch {branch_name}: {str(e)}")
        raise
    
    # Print repository info with unique commit count
    DBM.i(f"\t\t{repo_key}: {repo_commit_count} commits")

    if not EM.DEBUG_RUN:
        await sleep(0.4)

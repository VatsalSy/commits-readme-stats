from asyncio import Task
from hashlib import md5
from json import dumps
from string import Template
from typing import Dict, List
import os

from httpx import AsyncClient

from .manager_environment import EnvironmentManager as EM
from .manager_debug import DebugManager as DBM

GITHUB_API_QUERIES = {
    "user_repository_list": """
query($username: String!) {
    user(login: $username) {
        repositories(
            first: 100,
            orderBy: {field: CREATED_AT, direction: DESC},
            ownerAffiliations: [OWNER],
            isFork: false
        ) {
            nodes {
                primaryLanguage {
                    name
                }
                name
                owner {
                    login
                }
                isPrivate
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
}
""",
    "repo_branch_list": """
query($owner: String!, $name: String!) {
    repository(owner: $owner, name: $name) {
        refs(first: 100, refPrefix: "refs/heads/") {
            nodes {
                name
            }
        }
    }
}
""",
    "repo_commit_list": """
query($owner: String!, $name: String!, $branch: String!) {
    repository(owner: $owner, name: $name) {
        ref(qualifiedName: $branch) {
            target {
                ... on Commit {
                    history(first: 100) {
                        nodes {
                            committedDate
                            oid
                            additions
                            deletions
                            author {
                                user {
                                    login
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
"""
}

class DownloadManager:
    _CLIENT: AsyncClient = None
    _REMOTE_RESOURCES_CACHE = {}
    _REMOTE_RESOURCES: List[Task] = []
    target_username: str = None

    @staticmethod
    async def init(username: str):
        """Initialize the download manager with GitHub API client."""
        DBM.i("Initializing download manager...")
        DownloadManager.target_username = username
        DownloadManager._CLIENT = AsyncClient(
            headers={
                "Authorization": f"Bearer {EM.GH_TOKEN}",
                "Content-Type": "application/json",
            }
        )
        DBM.g("Download manager initialized!")

    @staticmethod
    async def get_remote_graphql(query: str, **kwargs) -> Dict:
        """
        Get remote GraphQL query result.
        Caches results for future use.
        """
        key = f"{query}_{md5(dumps(kwargs, sort_keys=True).encode('utf-8')).digest()}"
        if key not in DownloadManager._REMOTE_RESOURCES_CACHE:
            res = await DownloadManager._fetch_graphql_query(query, kwargs)
            DownloadManager._REMOTE_RESOURCES_CACHE[key] = res
        else:
            res = DownloadManager._REMOTE_RESOURCES_CACHE[key]
        return res

    @staticmethod
    async def _fetch_graphql_query(query: str, variables: Dict) -> Dict:
        """Execute a GraphQL query and return the results."""
        if query not in GITHUB_API_QUERIES:
            raise ValueError(f"Unknown query: {query}")

        query_str = GITHUB_API_QUERIES[query]
        DBM.i(f"Sending GraphQL query: {query}")
        response = await DownloadManager._CLIENT.post(
            "https://api.github.com/graphql",
            json={
                "query": query_str,
                "variables": variables
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"GraphQL query failed: {response.text}")
            
        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
            
        # Handle different query types
        if query == "user_repository_list":
            return data["data"]["user"]["repositories"]["nodes"]
        elif query == "repo_branch_list":
            return data["data"]["repository"]["refs"]["nodes"]
        elif query == "repo_commit_list":
            return data["data"]  # Return full data structure for commits
        else:
            return data["data"]

    @staticmethod
    async def close_remote_resources():
        """Clean up resources."""
        if DownloadManager._CLIENT:
            await DownloadManager._CLIENT.aclose()

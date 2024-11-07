from asyncio import Task
from hashlib import md5
from json import dumps
from string import Template
from typing import Dict, List
import os
from time import sleep

from httpx import AsyncClient

from .manager_environment import EnvironmentManager as EM
from .manager_debug import DebugManager as DBM
from .manager_token import TokenManager

GITHUB_API_QUERIES = {
    "user_repository_list": """
query($username: String!, $after: String) {
    user(login: $username) {
        repositories(
            first: 100,
            after: $after,
            orderBy: {field: CREATED_AT, direction: DESC},
            ownerAffiliations: [OWNER, ORGANIZATION_MEMBER, COLLABORATOR],
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
        
        Args:
            query: The name of the predefined query to execute
            **kwargs: Variables to pass to the query
            
        Returns:
            Dict containing the query results
            
        Raises:
            ValueError: If query name is invalid or variables are missing/invalid
        """
        # Validate query name
        if not isinstance(query, str):
            raise ValueError("Query name must be a string")
        
        if query not in GITHUB_API_QUERIES:
            raise ValueError(f"Unknown query: {query}")
            
        # Validate required variables based on query type
        required_vars = {
            'user_repository_list': ['username'],
            'repo_branch_list': ['owner', 'name'],
            'repo_commit_list': ['owner', 'name', 'branch']
        }
        
        missing_vars = [var for var in required_vars[query] if var not in kwargs]
        if missing_vars:
            raise ValueError(f"Missing required variables for {query}: {', '.join(missing_vars)}")
            
        # Validate variable types and content
        for var, value in kwargs.items():
            if not isinstance(value, str):
                raise ValueError(f"Variable {var} must be a string")
            if not value.strip():
                raise ValueError(f"Variable {var} cannot be empty")
            # Basic sanitization - remove any control characters
            kwargs[var] = ''.join(char for char in value if ord(char) >= 32)
                
        # Generate cache key
        key = f"{query}_{md5(dumps(kwargs, sort_keys=True).encode('utf-8')).digest()}"
        
        if key not in DownloadManager._REMOTE_RESOURCES_CACHE:
            res = await DownloadManager._fetch_graphql_query(query, kwargs)
            DownloadManager._REMOTE_RESOURCES_CACHE[key] = res
        else:
            res = DownloadManager._REMOTE_RESOURCES_CACHE[key]
        return res

    @staticmethod
    async def _fetch_graphql_query(query: str, variables: Dict) -> Dict:
        """
        Execute a GraphQL query and return the results.
        
        Args:
            query: The name of the predefined query to execute
            variables: Dictionary of variables for the query
            
        Returns:
            Dict containing the query results
            
        Raises:
            Exception: If query fails or rate limit is exceeded
        """
        query_str = GITHUB_API_QUERIES[query]
        all_nodes = []
        has_next_page = True
        end_cursor = None
        retry_count = 0
        max_retries = 3
        
        while has_next_page and retry_count < max_retries:
            try:
                if end_cursor:
                    variables["after"] = end_cursor

                DBM.i(f"Sending GraphQL query: {query} {'with cursor' if end_cursor else ''}")
                
                # Add timeout to prevent hanging
                response = await DownloadManager._CLIENT.post(
                    "https://api.github.com/graphql",
                    json={
                        "query": query_str,
                        "variables": variables
                    },
                    timeout=30.0  # 30 second timeout
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    DBM.w(f"Rate limit exceeded, waiting {retry_after} seconds")
                    await sleep(retry_after)
                    retry_count += 1
                    continue
                    
                if response.status_code != 200:
                    error_text = TokenManager.mask_token(response.text)
                    raise Exception(f"GraphQL query failed: {error_text}")
                    
                data = response.json()
                if "errors" in data:
                    error_text = TokenManager.mask_token(str(data['errors']))
                    raise Exception(f"GraphQL errors: {error_text}")
                
                # Reset retry count on successful request    
                retry_count = 0
                
                # Handle pagination for different query types
                if query == "user_repository_list":
                    repos = data["data"]["user"]["repositories"]
                    all_nodes.extend(repos["nodes"])
                    has_next_page = repos["pageInfo"]["hasNextPage"]
                    end_cursor = repos["pageInfo"]["endCursor"]
                else:
                    return data["data"]
                    
            except Exception as e:
                error_msg = TokenManager.mask_token(str(e))
                DBM.p(f"Error executing GraphQL query: {error_msg}")
                raise
                
        if retry_count >= max_retries:
            raise Exception("Max retries exceeded for GraphQL query")
            
        return all_nodes if query == "user_repository_list" else data["data"]

    @staticmethod
    async def close_remote_resources():
        """Clean up resources."""
        if DownloadManager._CLIENT:
            await DownloadManager._CLIENT.aclose()

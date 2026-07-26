from asyncio import Task
from hashlib import sha256
from json import dumps
from time import monotonic, time
from typing import Dict, List
from asyncio import sleep
from copy import deepcopy

from httpx import AsyncClient

from .manager_environment import EnvironmentManager as EM
from .manager_debug import DebugManager as DBM
from .manager_token import TokenManager

GITHUB_API_QUERIES = {
    "user_identity": """
query($username: String!) {
    user(login: $username) {
        id
        login
        createdAt
    }
}
""",
    "user_repository_list": """
query($username: String!, $after: String) {
    user(login: $username) {
        repositories(
            first: 100,
            after: $after,
            orderBy: {field: CREATED_AT, direction: DESC},
            ownerAffiliations: [OWNER, ORGANIZATION_MEMBER, COLLABORATOR]
        ) {
            nodes {
                name
                nameWithOwner
                owner {
                    login
                }
                isPrivate
                defaultBranchRef {
                    name
                }
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
query($owner: String!, $name: String!, $after: String) {
    repository(owner: $owner, name: $name) {
        refs(first: 100, after: $after, refPrefix: "refs/heads/") {
            nodes {
                name
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
}
""",
    "repo_commit_list": """
query($owner: String!, $name: String!, $branch: String!, $authorId: ID!, $after: String) {
    repository(owner: $owner, name: $name) {
        ref(qualifiedName: $branch) {
            target {
                ... on Commit {
                    history(first: 100, after: $after, author: {id: $authorId}) {
                        nodes {
                            committedDate
                            oid
                            author {
                                user {
                                    login
                                }
                            }
                        }
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                    }
                }
            }
        }
    }
}
""",
    "repo_commit_list_window": """
query(
    $owner: String!,
    $name: String!,
    $branch: String!,
    $authorId: ID!,
    $since: GitTimestamp!,
    $until: GitTimestamp!,
    $after: String
) {
    repository(owner: $owner, name: $name) {
        ref(qualifiedName: $branch) {
            target {
                ... on Commit {
                    history(
                        first: 100,
                        after: $after,
                        author: {id: $authorId},
                        since: $since,
                        until: $until
                    ) {
                        nodes {
                            committedDate
                            oid
                            author {
                                user {
                                    login
                                }
                            }
                        }
                        pageInfo {
                            hasNextPage
                            endCursor
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
    _COLLECTION_STARTED_AT = 0.0
    _GRAPHQL_ATTEMPTS = 0
    _LAST_GRAPHQL_REQUEST_AT = 0.0
    _MAX_COLLECTION_SECONDS = 45 * 60
    _MAX_GRAPHQL_ATTEMPTS = 1500
    _MAX_HISTORY_PAGES = 100
    _MAX_REPOSITORY_PAGES = 5
    _MIN_GRAPHQL_REQUEST_INTERVAL_SECONDS = 1.25
    target_username: str = None

    @classmethod
    async def init(cls, username: str):
        """Initialize download manager with headers"""
        cls.target_username = username
        cls._COLLECTION_STARTED_AT = monotonic()
        cls._GRAPHQL_ATTEMPTS = 0
        cls._LAST_GRAPHQL_REQUEST_AT = 0.0
        cls._REMOTE_RESOURCES_CACHE = {}
        cls.headers = {
            "Authorization": f"Bearer {EM.GH_COMMIT_TOKEN}",
            "Content-Type": "application/json",
        }
        cls._CLIENT = AsyncClient(
            headers=cls.headers
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
            'user_identity': ['username'],
            'user_repository_list': ['username'],
            'repo_branch_list': ['owner', 'name'],
            'repo_commit_list': ['owner', 'name', 'branch', 'authorId'],
            'repo_commit_list_window': [
                'owner',
                'name',
                'branch',
                'authorId',
                'since',
                'until',
            ],
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
        key = f"{query}_{sha256(dumps(kwargs, sort_keys=True).encode('utf-8')).hexdigest()}"
        
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
        max_retries = 5
        result = None
        base_variables = variables.copy()
        page_count = 0
        seen_cursors = set()
        
        while has_next_page and retry_count < max_retries:
            try:
                max_pages = (
                    DownloadManager._MAX_REPOSITORY_PAGES
                    if query == "user_repository_list"
                    else DownloadManager._MAX_HISTORY_PAGES
                )
                if query != "user_identity" and page_count >= max_pages:
                    raise Exception(
                        f"Page budget exceeded for GraphQL query: {query}"
                    )

                request_variables = base_variables.copy()
                if end_cursor:
                    request_variables["after"] = end_cursor

                DBM.i(f"Sending GraphQL query: {query} {'with cursor' if end_cursor else ''}")

                elapsed = monotonic() - DownloadManager._LAST_GRAPHQL_REQUEST_AT
                if elapsed < DownloadManager._MIN_GRAPHQL_REQUEST_INTERVAL_SECONDS:
                    await sleep(
                        DownloadManager._MIN_GRAPHQL_REQUEST_INTERVAL_SECONDS - elapsed
                    )
                DownloadManager._LAST_GRAPHQL_REQUEST_AT = monotonic()
                DownloadManager._enforce_collection_budget()
                DownloadManager._GRAPHQL_ATTEMPTS += 1

                # Add timeout to prevent hanging
                response = await DownloadManager._CLIENT.post(
                    "https://api.github.com/graphql",
                    json={
                        "query": query_str,
                        "variables": request_variables
                    },
                    timeout=30.0  # 30 second timeout
                )
                
                try:
                    response_data = response.json()
                except Exception:
                    response_data = {}
                response_error_text = str(response_data.get("message", ""))
                response_error_text += " " + str(response_data.get("errors", ""))

                # GitHub returns secondary limits as HTTP 403, HTTP 429, or a
                # GraphQL error inside an otherwise successful HTTP 200.
                is_rate_limited = (
                    response.status_code == 429
                    or (
                        response.status_code == 403
                        and DownloadManager._is_rate_limit_error(response_error_text)
                    )
                    or (
                        response.status_code == 200
                        and "errors" in response_data
                        and DownloadManager._is_rate_limit_error(response_error_text)
                    )
                )
                if is_rate_limited:
                    retry_count += 1
                    retry_after = DownloadManager._rate_limit_retry_after(
                        response,
                        retry_count,
                    )
                    DBM.w(
                        "GitHub API rate limit reached; "
                        f"retry {retry_count}/{max_retries} in {retry_after}s"
                    )
                    if retry_count >= max_retries:
                        break
                    await sleep(retry_after)
                    continue

                # Handle transient server errors with exponential backoff
                if response.status_code in (502, 503, 504):
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = min(2 ** retry_count, 32)  # 2s, 4s, 8s, 16s, 32s
                        DBM.w(f"Server error {response.status_code}, retry {retry_count}/{max_retries} in {wait_time}s")
                        await sleep(wait_time)
                        continue

                if response.status_code != 200:
                    # Mask sensitive information before logging or raising
                    status_code = response.status_code
                    masked_headers = {
                        k: TokenManager.mask_token(str(v)) 
                        for k, v in response.headers.items()
                    }
                    
                    try:
                        # Try to get JSON response for better error details
                        error_data = response.json()
                        masked_error = TokenManager.mask_token(str(error_data.get('message', '')))
                    except:
                        # Fallback to basic error if JSON parsing fails
                        masked_error = f"HTTP {status_code}"
                        
                    error_msg = f"GraphQL query failed: {masked_error}"
                    if EM.DEBUG_RUN:
                        error_msg += f"\nHeaders: {masked_headers}"
                        
                    raise Exception(error_msg)
                    
                data = response_data
                if "errors" in data:
                    error_text = TokenManager.mask_token(str(data['errors']))
                    raise Exception(f"GraphQL errors: {error_text}")
                
                # Reset retry count on successful request    
                retry_count = 0
                
                page_data = data["data"]
                if query == "user_identity":
                    return page_data

                # Aggregate pages while retaining the response shapes used by
                # the existing collectors.
                if query == "user_repository_list":
                    connection = page_data["user"]["repositories"]
                elif query == "repo_branch_list":
                    connection = page_data["repository"]["refs"]
                else:
                    connection = page_data["repository"]["ref"]["target"]["history"]

                if result is None:
                    result = deepcopy(page_data)
                all_nodes.extend(connection["nodes"])
                page_count += 1
                has_next_page = connection["pageInfo"]["hasNextPage"]
                next_cursor = connection["pageInfo"]["endCursor"]
                if has_next_page:
                    if (
                        not next_cursor
                        or next_cursor == end_cursor
                        or next_cursor in seen_cursors
                    ):
                        raise Exception(
                            f"Invalid pagination cursor for GraphQL query: {query}"
                        )
                    seen_cursors.add(next_cursor)
                end_cursor = next_cursor
                    
            except Exception as e:
                error_msg = TokenManager.mask_token(str(e))
                DBM.p(f"Error executing GraphQL query: {error_msg}")
                raise
                
        if retry_count >= max_retries:
            raise Exception("Max retries exceeded for GraphQL query")

        # Never return a truncated connection if pagination stopped early.
        if has_next_page:
            raise Exception(f"Incomplete pagination for GraphQL query: {query}")
            
        if query == "user_repository_list":
            return all_nodes
        if query == "repo_branch_list":
            result["repository"]["refs"]["nodes"] = all_nodes
        elif query in ("repo_commit_list", "repo_commit_list_window"):
            result["repository"]["ref"]["target"]["history"]["nodes"] = all_nodes
        return result

    @staticmethod
    def _is_rate_limit_error(message: str) -> bool:
        """Return whether a GitHub error describes primary or secondary limiting."""
        normalized = message.lower()
        return any(
            marker in normalized
            for marker in (
                "rate limit",
                "abuse detection",
                "temporarily blocked",
            )
        )

    @staticmethod
    def _rate_limit_retry_after(response, retry_count: int) -> int:
        """Choose a conservative wait using GitHub headers when available."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(1, int(retry_after))
            except (TypeError, ValueError):
                pass

        if response.headers.get("x-ratelimit-remaining") == "0":
            try:
                reset_at = int(response.headers["x-ratelimit-reset"])
                return max(1, reset_at - int(time()) + 5)
            except (KeyError, TypeError, ValueError):
                pass

        return min(60 * (2 ** (retry_count - 1)), 15 * 60)

    @staticmethod
    def _enforce_collection_budget():
        """Abort before an exhaustive crawl can overrun its global limits."""
        if (
            DownloadManager._GRAPHQL_ATTEMPTS
            >= DownloadManager._MAX_GRAPHQL_ATTEMPTS
        ):
            raise Exception("GraphQL request budget exceeded")

        if DownloadManager._COLLECTION_STARTED_AT == 0.0:
            DownloadManager._COLLECTION_STARTED_AT = monotonic()
        elapsed = monotonic() - DownloadManager._COLLECTION_STARTED_AT
        if elapsed >= DownloadManager._MAX_COLLECTION_SECONDS:
            raise Exception("GraphQL collection time budget exceeded")

    @staticmethod
    async def close_remote_resources():
        """Clean up resources."""
        if DownloadManager._CLIENT:
            await DownloadManager._CLIENT.aclose()

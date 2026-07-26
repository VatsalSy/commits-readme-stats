from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from sources.graphics_list_formatter import make_commit_day_time_list
from sources.manager_download import DownloadManager, GITHUB_API_QUERIES
from sources.manager_environment import EnvironmentManager
from sources.manager_file import FileManager
from sources.yearly_commit_calculator import (
    calculate_commit_data,
    get_default_branch_commits,
    update_data_with_commit_stats,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.status_code = status_code
        self.headers = {}
        self._payload = payload

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_commit_history_paginates_and_preserves_response_shape():
    first_page = {
        "data": {
            "repository": {
                "ref": {
                    "target": {
                        "history": {
                            "nodes": [{"oid": "one"}],
                            "pageInfo": {
                                "hasNextPage": True,
                                "endCursor": "cursor-1",
                            },
                        }
                    }
                }
            }
        }
    }
    second_page = {
        "data": {
            "repository": {
                "ref": {
                    "target": {
                        "history": {
                            "nodes": [{"oid": "two"}],
                            "pageInfo": {
                                "hasNextPage": False,
                                "endCursor": "cursor-2",
                            },
                        }
                    }
                }
            }
        }
    }
    client = AsyncMock()
    client.post.side_effect = [
        FakeResponse(first_page),
        FakeResponse(second_page),
    ]

    with patch.object(DownloadManager, "_CLIENT", client):
        result = await DownloadManager._fetch_graphql_query(
            "repo_commit_list",
            {
                "owner": "owner",
                "name": "repo",
                "branch": "main",
                "authorId": "user-id",
            },
        )

    history = result["repository"]["ref"]["target"]["history"]
    assert [node["oid"] for node in history["nodes"]] == ["one", "two"]
    assert client.post.await_count == 2
    assert (
        client.post.await_args_list[1].kwargs["json"]["variables"]["after"]
        == "cursor-1"
    )


@pytest.mark.asyncio
async def test_branch_list_paginates():
    def page(nodes, has_next_page, end_cursor):
        return {
            "data": {
                "repository": {
                    "refs": {
                        "nodes": nodes,
                        "pageInfo": {
                            "hasNextPage": has_next_page,
                            "endCursor": end_cursor,
                        },
                    }
                }
            }
        }

    client = AsyncMock()
    client.post.side_effect = [
        FakeResponse(page([{"name": "main"}], True, "cursor-1")),
        FakeResponse(page([{"name": "feature"}], False, "cursor-2")),
    ]

    with patch.object(DownloadManager, "_CLIENT", client):
        result = await DownloadManager._fetch_graphql_query(
            "repo_branch_list",
            {"owner": "owner", "name": "repo"},
        )

    assert [node["name"] for node in result["repository"]["refs"]["nodes"]] == [
        "main",
        "feature",
    ]
    assert client.post.await_count == 2


@pytest.mark.asyncio
async def test_pagination_fails_closed_after_retry_exhaustion():
    client = AsyncMock()
    client.post.return_value = FakeResponse({}, status_code=502)

    with patch.object(DownloadManager, "_CLIENT", client), patch(
        "sources.manager_download.sleep", new=AsyncMock()
    ):
        with pytest.raises(Exception, match="GraphQL query failed"):
            await DownloadManager._fetch_graphql_query(
                "repo_commit_list",
                {
                    "owner": "owner",
                    "name": "repo",
                    "branch": "main",
                    "authorId": "user-id",
                },
            )

    assert client.post.await_count == 5


@pytest.mark.asyncio
async def test_secondary_rate_limit_retries_the_current_page():
    limited = {
        "errors": [
            {
                "type": "RATE_LIMITED",
                "message": "You have exceeded a secondary rate limit.",
            }
        ]
    }
    success = {
        "data": {
            "repository": {
                "ref": {
                    "target": {
                        "history": {
                            "nodes": [{"oid": "one"}],
                            "pageInfo": {
                                "hasNextPage": False,
                                "endCursor": "cursor-1",
                            },
                        }
                    }
                }
            }
        }
    }
    client = AsyncMock()
    client.post.side_effect = [
        FakeResponse(limited),
        FakeResponse(success),
    ]
    sleeper = AsyncMock()

    with patch.object(DownloadManager, "_CLIENT", client), patch.object(
        DownloadManager, "_MIN_GRAPHQL_REQUEST_INTERVAL_SECONDS", 0
    ), patch("sources.manager_download.sleep", new=sleeper):
        result = await DownloadManager._fetch_graphql_query(
            "repo_commit_list",
            {
                "owner": "owner",
                "name": "repo",
                "branch": "main",
                "authorId": "user-id",
            },
        )

    history = result["repository"]["ref"]["target"]["history"]
    assert [node["oid"] for node in history["nodes"]] == ["one"]
    assert client.post.await_count == 2
    sleeper.assert_awaited_once_with(60)


@pytest.mark.asyncio
async def test_default_branch_history_deduplicates_across_forks():
    repositories = [
        {
            "name": "same-name",
            "nameWithOwner": "one/same-name",
            "owner": {"login": "one"},
            "primaryLanguage": {"name": "Python"},
            "defaultBranchRef": {"name": "main"},
        },
        {
            "name": "same-name",
            "nameWithOwner": "two/same-name",
            "owner": {"login": "two"},
            "primaryLanguage": {"name": "Python"},
            "defaultBranchRef": {"name": "main"},
        },
    ]
    commits = {
        ("one", "main"): [
            {
                "oid": "shared",
                "committedDate": "2026-01-01T12:00:00Z",
                "additions": 1,
                "deletions": 0,
                "author": {"user": {"login": "VatsalSy"}},
            },
            {
                "oid": "one-only",
                "committedDate": "2026-01-02T12:00:00Z",
                "additions": 1,
                "deletions": 0,
                "author": {"user": {"login": "VatsalSy"}},
            },
        ],
        ("two", "main"): [
            {
                "oid": "shared",
                "committedDate": "2026-01-01T12:00:00Z",
                "additions": 1,
                "deletions": 0,
                "author": {"user": {"login": "VatsalSy"}},
            },
            {
                "oid": "two-only",
                "committedDate": "2026-01-03T12:00:00Z",
                "additions": 1,
                "deletions": 0,
                "author": {"user": {"login": "VatsalSy"}},
            },
        ],
    }

    async def graphql(query, **kwargs):
        nodes = commits[(kwargs["owner"], kwargs["branch"])]
        return {"repository": {"ref": {"target": {"history": {"nodes": nodes}}}}}

    yearly_data = {}
    date_data = {}
    seen_commit_oids = set()

    with patch.object(DownloadManager, "get_remote_graphql", side_effect=graphql):
        for repository in repositories:
            await update_data_with_commit_stats(
                repository,
                yearly_data,
                date_data,
                "VatsalSy",
                "user-id",
                seen_commit_oids,
                2016,
            )

    assert seen_commit_oids == {"shared", "one-only", "two-only"}
    assert set(date_data) == {"one/same-name", "two/same-name"}
    assert (
        sum(
            len(branch)
            for repository in date_data.values()
            for branch in repository.values()
        )
        == 3
    )

    with patch.object(EnvironmentManager, "SHOW_TOTAL_COMMITS", True), patch.object(
        EnvironmentManager, "SHOW_COMMIT", False
    ), patch.object(EnvironmentManager, "SHOW_DAYS_OF_WEEK", False):
        output = await make_commit_day_time_list("UTC", repositories, date_data)
    assert (
        "Accessible unique authored commits on repository default branches "
        "(last successful crawl): 3"
    ) in output


@pytest.mark.asyncio
async def test_repository_collection_propagates_default_branch_failure():
    repository = {
        "name": "repo",
        "nameWithOwner": "owner/repo",
        "owner": {"login": "owner"},
        "primaryLanguage": {"name": "Python"},
        "defaultBranchRef": {"name": "main"},
    }

    async def graphql(query, **kwargs):
        raise RuntimeError("branch failed")

    with patch.object(DownloadManager, "get_remote_graphql", side_effect=graphql):
        with pytest.raises(RuntimeError, match="branch failed"):
            await update_data_with_commit_stats(
                repository,
                {},
                {},
                "VatsalSy",
                "user-id",
                set(),
                2016,
            )


@pytest.mark.asyncio
async def test_empty_repository_skips_history_query():
    repository = {
        "name": "empty",
        "nameWithOwner": "owner/empty",
        "owner": {"login": "owner"},
        "primaryLanguage": None,
        "defaultBranchRef": None,
    }

    with patch.object(
        DownloadManager,
        "get_remote_graphql",
        new=AsyncMock(),
    ) as graphql:
        await update_data_with_commit_stats(
            repository,
            {},
            {},
            "VatsalSy",
            "user-id",
            set(),
            2016,
        )

    graphql.assert_not_awaited()


@pytest.mark.asyncio
async def test_large_history_5xx_falls_back_to_year_window():
    repository = {
        "name": "large",
        "nameWithOwner": "owner/large",
        "owner": {"login": "owner"},
    }
    windowed = {
        "repository": {
            "ref": {
                "target": {
                    "history": {
                        "nodes": [{"oid": "one"}],
                    }
                }
            }
        }
    }
    graphql = AsyncMock(
        side_effect=[
            RuntimeError("GraphQL query failed: HTTP 502"),
            windowed,
        ]
    )
    current_year = datetime.now().year

    with patch.object(DownloadManager, "get_remote_graphql", new=graphql):
        commits = await get_default_branch_commits(
            repository,
            "main",
            "user-id",
            current_year,
        )

    assert commits == [{"oid": "one"}]
    assert graphql.await_count == 2
    assert graphql.await_args_list[1].args == ("repo_commit_list_window",)
    assert graphql.await_args_list[1].kwargs["since"] == (
        f"{current_year}-01-01T00:00:00Z"
    )
    assert graphql.await_args_list[1].kwargs["until"] == (
        f"{current_year + 1}-01-01T00:00:00Z"
    )


@pytest.mark.asyncio
async def test_github_actions_runner_does_not_read_or_write_commit_cache():
    identity = {
        "user": {
            "id": "user-id",
            "createdAt": "2016-02-06T00:00:00Z",
        }
    }

    with patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}), patch.object(
        FileManager,
        "cache_binary",
    ) as cache_binary, patch.object(
        DownloadManager,
        "get_remote_graphql",
        new=AsyncMock(return_value=identity),
    ):
        await calculate_commit_data([], "VatsalSy")

    cache_binary.assert_not_called()


@pytest.mark.asyncio
async def test_pagination_rejects_missing_next_cursor():
    page = {
        "data": {
            "repository": {
                "ref": {
                    "target": {
                        "history": {
                            "nodes": [{"oid": "one"}],
                            "pageInfo": {
                                "hasNextPage": True,
                                "endCursor": None,
                            },
                        }
                    }
                }
            }
        }
    }
    client = AsyncMock()
    client.post.return_value = FakeResponse(page)

    with patch.object(DownloadManager, "_CLIENT", client), patch.object(
        DownloadManager, "_MIN_GRAPHQL_REQUEST_INTERVAL_SECONDS", 0
    ):
        with pytest.raises(Exception, match="Invalid pagination cursor"):
            await DownloadManager._fetch_graphql_query(
                "repo_commit_list",
                {
                    "owner": "owner",
                    "name": "repo",
                    "branch": "main",
                    "authorId": "user-id",
                },
            )


@pytest.mark.asyncio
async def test_history_page_budget_fails_closed():
    page = {
        "data": {
            "repository": {
                "ref": {
                    "target": {
                        "history": {
                            "nodes": [{"oid": "one"}],
                            "pageInfo": {
                                "hasNextPage": True,
                                "endCursor": "cursor-1",
                            },
                        }
                    }
                }
            }
        }
    }
    client = AsyncMock()
    client.post.return_value = FakeResponse(page)

    with patch.object(DownloadManager, "_CLIENT", client), patch.object(
        DownloadManager, "_MIN_GRAPHQL_REQUEST_INTERVAL_SECONDS", 0
    ), patch.object(DownloadManager, "_MAX_HISTORY_PAGES", 1):
        with pytest.raises(Exception, match="Page budget exceeded"):
            await DownloadManager._fetch_graphql_query(
                "repo_commit_list",
                {
                    "owner": "owner",
                    "name": "repo",
                    "branch": "main",
                    "authorId": "user-id",
                },
            )

    assert client.post.await_count == 1


def test_commit_cache_expires(tmp_path, monkeypatch):
    monkeypatch.setattr(FileManager, "ASSETS_DIR", str(tmp_path))
    monkeypatch.setattr(FileManager, "_ENCRYPTION_KEY", None)
    FileManager.cache_binary("commits.json", {"count": 1}, assets=True)
    cache_path = Path(tmp_path, "commits.json")

    with patch(
        "sources.manager_file.time.time", return_value=cache_path.stat().st_mtime + 11
    ):
        assert (
            FileManager.cache_binary(
                "commits.json",
                assets=True,
                max_age_seconds=10,
            )
            is None
        )


def test_commit_query_filters_by_github_user_identity():
    assert "author: {id: $authorId}" in GITHUB_API_QUERIES["repo_commit_list"]
    assert "defaultBranchRef" in GITHUB_API_QUERIES["user_repository_list"]
    for query_name in ("repo_commit_list", "repo_commit_list_window"):
        assert "additions" not in GITHUB_API_QUERIES[query_name]
        assert "deletions" not in GITHUB_API_QUERIES[query_name]


def test_collection_safety_budgets_are_bounded():
    assert DownloadManager._MAX_REPOSITORY_PAGES == 5
    assert DownloadManager._MAX_HISTORY_PAGES == 100
    assert DownloadManager._MAX_GRAPHQL_ATTEMPTS == 1500
    assert DownloadManager._MAX_COLLECTION_SECONDS == 45 * 60

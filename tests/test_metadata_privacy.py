from unittest.mock import patch

import pytest

from sources.manager_download import (
    GITHUB_API_QUERIES,
    countable_repository_nodes,
    public_repository_nodes,
    repository_privacy_filter,
)
from sources.manager_token import TokenManager


def test_repository_collection_is_public_only():
    assert "privacy: $privacy" in GITHUB_API_QUERIES["user_repository_list"]
    assert repository_privacy_filter(False) == "PUBLIC"
    expected = {"name": "example", "isPrivate": False}
    assert public_repository_nodes([
        None, {}, {"isPrivate": None}, {"isPrivate": True}, expected,
    ]) == [expected]


def test_git_credentials_are_scoped_to_https_github_subprocess():
    with patch.object(TokenManager, "get_token", return_value="synthetic-fixture"):
        credentials = TokenManager.get_credentials_helper()
    assert credentials["GIT_CONFIG_KEY_0"] == "credential.helper"
    assert credentials["GIT_CONFIG_VALUE_0"] == ""
    assert credentials["GIT_CONFIG_KEY_1"] == "http.https://github.com/.extraheader"
    assert credentials["GIT_CONFIG_VALUE_1"].startswith("Authorization: Basic ")
    assert credentials["GIT_CONFIG_KEY_2"] == "http.followRedirects"
    assert credentials["GIT_CONFIG_VALUE_2"] == "false"
    assert credentials["GIT_TERMINAL_PROMPT"] == "0"


def test_private_repositories_count_only_on_opt_in():
    private = {"name": "example", "isPrivate": True}
    public = {"name": "other", "isPrivate": False}
    assert repository_privacy_filter(True) is None
    assert countable_repository_nodes([None, private, public], True) == [private, public]
    assert countable_repository_nodes([None, private, public], False) == [public]


def test_private_opt_in_requires_a_separate_push_credential(monkeypatch):
    monkeypatch.delenv("INPUT_GH_PUSH_TOKEN", raising=False)
    with patch.object(TokenManager, "get_token", return_value="synthetic-crawl-fixture"):
        assert TokenManager.get_push_token() == "synthetic-crawl-fixture"
        with pytest.raises(ValueError, match="GH_PUSH_TOKEN"):
            TokenManager.get_push_token(require_separate=True)


def test_push_uses_the_push_credential_and_never_the_crawl_token(monkeypatch):
    from base64 import b64decode

    monkeypatch.setenv("INPUT_GH_PUSH_TOKEN", "synthetic-push-fixture-0000")
    monkeypatch.setattr(TokenManager, "_push_token", None)
    with patch.object(TokenManager, "get_token", return_value="synthetic-crawl-fixture"):
        credentials = TokenManager.get_credentials_helper()
    header = credentials["GIT_CONFIG_VALUE_1"].removeprefix("Authorization: Basic ")
    assert b64decode(header).decode() == "x-access-token:synthetic-push-fixture-0000"
    assert TokenManager.mask_token("push synthetic-push-fixture-0000 done") == "push ******** done"


def test_malformed_push_credential_is_rejected(monkeypatch):
    monkeypatch.setenv("INPUT_GH_PUSH_TOKEN", "short token")
    with pytest.raises(ValueError, match="Invalid GH_PUSH_TOKEN"):
        TokenManager.get_push_token()


class _Response:
    status_code = 200
    headers = {}

    def json(self):
        nodes = [{"name": "open", "isPrivate": False}, {"name": "closed", "isPrivate": True}]
        page = {"hasNextPage": False, "endCursor": None}
        return {"data": {"user": {"repositories": {"nodes": nodes, "pageInfo": page}}}}


@pytest.mark.asyncio
@pytest.mark.parametrize("include_private, sent_privacy, names", [
    (False, "PUBLIC", ["open"]),
    (True, None, ["open", "closed"]),
])
async def test_repository_request_and_result_follow_the_opt_in(include_private, sent_privacy, names, caplog):
    from unittest.mock import AsyncMock
    from sources.manager_download import DownloadManager
    from sources.manager_environment import EnvironmentManager

    client = AsyncMock()
    client.post.return_value = _Response()
    with patch.object(DownloadManager, "_CLIENT", client), \
            patch.object(EnvironmentManager, "INCLUDE_PRIVATE", include_private), \
            caplog.at_level("DEBUG"):
        nodes = await DownloadManager._fetch_graphql_query("user_repository_list", {"username": "owner"})

    assert [node["name"] for node in nodes] == names
    assert client.post.await_args.kwargs["json"]["variables"].get("privacy") == sent_privacy
    assert "closed" not in caplog.text and "open" not in caplog.text


def test_clone_does_not_leave_credentials_on_the_repository_object(tmp_path, monkeypatch):
    from unittest.mock import MagicMock
    from git import Repo
    from sources import manager_github
    from sources.manager_github import GitHubManager

    source = Repo.init(tmp_path / "source")
    (tmp_path / "source" / "README.md").write_text("fixture")
    source.index.add(["README.md"])
    source.index.commit("fixture")
    real_clone = Repo.clone_from

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("INPUT_GH_PUSH_TOKEN", "synthetic-push-fixture-0000")
    github = MagicMock()
    github.get_user.return_value.login = "owner"
    with patch.object(manager_github, "Github", return_value=github), \
            patch.object(TokenManager, "get_token", return_value="synthetic-crawl-fixture"), \
            patch.object(Repo, "clone_from", side_effect=lambda url, **kw: real_clone(str(tmp_path / "source"), **kw)):
        GitHubManager.prepare_github_env()

    assert not any(key.startswith("GIT_CONFIG") for key in GitHubManager.REPO.git.environment())


def test_local_cache_is_keyed_by_privacy_mode():
    import inspect
    from sources import yearly_commit_calculator

    assert "EM.INCLUDE_PRIVATE" in inspect.getsource(yearly_commit_calculator.calculate_commit_data)

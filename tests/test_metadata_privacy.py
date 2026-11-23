from unittest.mock import patch

from sources.manager_download import GITHUB_API_QUERIES, public_repository_nodes
from sources.manager_token import TokenManager


def test_repository_collection_is_public_only():
    assert "privacy: PUBLIC" in GITHUB_API_QUERIES["user_repository_list"]
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

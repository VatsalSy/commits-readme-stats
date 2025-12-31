"""
Tests for WakaTime integration flow in sources.main.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Add parent directory to path to make sources a package
sys.path.insert(0, str(Path(__file__).parent.parent))

import sources.main as main_module


@pytest.mark.asyncio
async def test_get_wakatime_stats_not_configured_returns_empty():
    with patch.object(main_module.WakaTimeManager, "is_configured", return_value=False), \
         patch.object(main_module.WakaTimeManager, "fetch_stats", new=AsyncMock()) as fetch_mock, \
         patch.object(main_module.WakaTimeManager, "close", new=AsyncMock()):
        result = await main_module.get_wakatime_stats()
        assert result == ""
        fetch_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_wakatime_stats_no_activity_returns_no_activity():
    no_activity = "NO_ACTIVITY"
    with patch.object(main_module.WakaTimeManager, "is_configured", return_value=True), \
         patch.object(main_module.WakaTimeManager, "fetch_stats", new=AsyncMock(return_value={
             "languages": [],
             "editors": [],
             "projects": [],
             "operating_systems": [],
         })), \
         patch.object(main_module.WakaTimeManager, "close", new=AsyncMock()), \
         patch.object(main_module, "format_no_activity", return_value=no_activity):
        result = await main_module.get_wakatime_stats()
        assert result == no_activity


@pytest.mark.asyncio
async def test_get_wakatime_stats_formats_data():
    formatted = "FORMATTED"
    mock_data = {
        "languages": [{"name": "Python", "percent": 100.0}],
        "editors": [],
        "projects": [],
        "operating_systems": [],
    }
    mock_flags = {"show_language": True}
    with patch.object(main_module.WakaTimeManager, "is_configured", return_value=True), \
         patch.object(main_module.WakaTimeManager, "fetch_stats", new=AsyncMock(return_value=mock_data)), \
         patch.object(main_module.WakaTimeManager, "get_show_flags", return_value=mock_flags), \
         patch.object(main_module.WakaTimeManager, "close", new=AsyncMock()), \
         patch.object(main_module, "format_wakatime_stats", return_value=formatted) as format_mock:
        result = await main_module.get_wakatime_stats()
        assert result == formatted
        format_mock.assert_called_once_with(mock_data, mock_flags)


@pytest.mark.asyncio
async def test_get_wakatime_stats_fetch_returns_none():
    """Should return empty string when fetch_stats returns None."""
    with patch.object(main_module.WakaTimeManager, "is_configured", return_value=True), \
         patch.object(main_module.WakaTimeManager, "fetch_stats", new=AsyncMock(return_value=None)), \
         patch.object(main_module.WakaTimeManager, "close", new=AsyncMock()) as close_mock:
        result = await main_module.get_wakatime_stats()
        assert result == ""
        close_mock.assert_called_once()


@pytest.mark.asyncio
async def test_get_wakatime_stats_handles_request_error():
    """Should return empty string and call close when fetch_stats raises RequestError."""
    from httpx import RequestError

    with patch.object(main_module.WakaTimeManager, "is_configured", return_value=True), \
         patch.object(main_module.WakaTimeManager, "fetch_stats", new=AsyncMock(side_effect=RequestError("Connection failed"))), \
         patch.object(main_module.WakaTimeManager, "close", new=AsyncMock()) as close_mock:
        result = await main_module.get_wakatime_stats()
        assert result == ""
        close_mock.assert_called_once()


@pytest.mark.asyncio
async def test_get_wakatime_stats_handles_json_error():
    """Should return empty string and call close when fetch_stats raises JSONDecodeError."""
    from json import JSONDecodeError

    with patch.object(main_module.WakaTimeManager, "is_configured", return_value=True), \
         patch.object(main_module.WakaTimeManager, "fetch_stats", new=AsyncMock(side_effect=JSONDecodeError("Invalid", "", 0))), \
         patch.object(main_module.WakaTimeManager, "close", new=AsyncMock()) as close_mock:
        result = await main_module.get_wakatime_stats()
        assert result == ""
        close_mock.assert_called_once()


@pytest.fixture
def main_test_setup(monkeypatch):
    """Common setup for main() tests with mocked environment and managers."""
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "")
    monkeypatch.setattr(main_module.EM, "USERNAME", "test-user", raising=False)
    monkeypatch.setattr(main_module.EM, "DEBUG_RUN", False, raising=False)


@pytest.mark.asyncio
async def test_main_updates_both_sections_when_wakatime_present(main_test_setup):
    with patch.object(main_module, "init_debug_manager"), \
         patch.object(main_module.EM, "init"), \
         patch.object(main_module, "init_github_manager"), \
         patch.object(main_module, "init_localization_manager"), \
         patch.object(main_module.DM, "init", new=AsyncMock()), \
         patch.object(main_module.DM, "close_remote_resources", new=AsyncMock()), \
         patch.object(main_module, "get_token_user", return_value=None), \
         patch.object(main_module.TokenManager, "get_token", return_value=None), \
         patch.object(main_module, "get_stats", new=AsyncMock(return_value="commit-stats")), \
         patch.object(main_module, "get_wakatime_stats", new=AsyncMock(return_value="wakatime-stats")), \
         patch.object(main_module.GHM, "update_readme") as update_mock, \
         patch.object(main_module.GHM, "commit_update") as commit_mock:
        await main_module.main()

        assert update_mock.call_count == 2
        update_mock.assert_any_call("commit-stats")
        update_mock.assert_any_call("wakatime-stats", section_name="wakatime")
        commit_mock.assert_called_once()


@pytest.mark.asyncio
async def test_main_skips_wakatime_update_when_empty(main_test_setup):
    with patch.object(main_module, "init_debug_manager"), \
         patch.object(main_module.EM, "init"), \
         patch.object(main_module, "init_github_manager"), \
         patch.object(main_module, "init_localization_manager"), \
         patch.object(main_module.DM, "init", new=AsyncMock()), \
         patch.object(main_module.DM, "close_remote_resources", new=AsyncMock()), \
         patch.object(main_module, "get_token_user", return_value=None), \
         patch.object(main_module.TokenManager, "get_token", return_value=None), \
         patch.object(main_module, "get_stats", new=AsyncMock(return_value="commit-stats")), \
         patch.object(main_module, "get_wakatime_stats", new=AsyncMock(return_value="")), \
         patch.object(main_module.GHM, "update_readme") as update_mock, \
         patch.object(main_module.GHM, "commit_update") as commit_mock:
        await main_module.main()

        update_mock.assert_called_once_with("commit-stats")
        commit_mock.assert_called_once()

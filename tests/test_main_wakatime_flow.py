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
         patch.object(main_module.WakaTimeManager, "fetch_stats", new=AsyncMock()) as fetch_mock:
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
    with patch.object(main_module.WakaTimeManager, "is_configured", return_value=True), \
         patch.object(main_module.WakaTimeManager, "fetch_stats", new=AsyncMock(return_value={
             "languages": [{"name": "Python", "percent": 100.0}],
             "editors": [],
             "projects": [],
             "operating_systems": [],
         })), \
         patch.object(main_module.WakaTimeManager, "get_show_flags", return_value={"show_language": True}), \
         patch.object(main_module.WakaTimeManager, "close", new=AsyncMock()), \
         patch.object(main_module, "format_wakatime_stats", return_value=formatted):
        result = await main_module.get_wakatime_stats()
        assert result == formatted


@pytest.mark.asyncio
async def test_main_updates_both_sections_when_wakatime_present(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "")
    monkeypatch.setattr(main_module.EM, "USERNAME", "test-user", raising=False)
    monkeypatch.setattr(main_module.EM, "DEBUG_RUN", False, raising=False)

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
async def test_main_skips_wakatime_update_when_empty(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "")
    monkeypatch.setattr(main_module.EM, "USERNAME", "test-user", raising=False)
    monkeypatch.setattr(main_module.EM, "DEBUG_RUN", False, raising=False)

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

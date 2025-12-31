"""
Unit tests for WakaTimeManager class.

Tests cover configuration checking, API key retrieval, HTTP response handling,
and display flag retrieval.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directory to path to make sources a package
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources.manager_wakatime import WakaTimeManager, WAKATIME_ENDPOINTS


class TestWakaTimeManagerConfiguration:
    """Test suite for WakaTimeManager configuration methods."""

    def test_is_configured_returns_true_when_both_set(self):
        """Should return True when API key is set and SHOW_WAKATIME is enabled."""
        with patch("sources.manager_wakatime.EM") as mock_em:
            mock_em.WAKATIME_API_KEY = "test_api_key"
            mock_em.SHOW_WAKATIME = True
            assert WakaTimeManager.is_configured() is True

    def test_is_configured_returns_false_when_key_missing(self):
        """Should return False when API key is not set."""
        with patch("sources.manager_wakatime.EM") as mock_em:
            mock_em.WAKATIME_API_KEY = None
            mock_em.SHOW_WAKATIME = True
            assert WakaTimeManager.is_configured() is False

    def test_is_configured_returns_false_when_show_disabled(self):
        """Should return False when SHOW_WAKATIME is disabled."""
        with patch("sources.manager_wakatime.EM") as mock_em:
            mock_em.WAKATIME_API_KEY = "test_api_key"
            mock_em.SHOW_WAKATIME = False
            assert WakaTimeManager.is_configured() is False

    def test_is_configured_returns_false_when_both_missing(self):
        """Should return False when both are not set."""
        with patch("sources.manager_wakatime.EM") as mock_em:
            mock_em.WAKATIME_API_KEY = None
            mock_em.SHOW_WAKATIME = False
            assert WakaTimeManager.is_configured() is False

    def test_get_api_key_returns_key_when_set(self):
        """Should return API key when set."""
        with patch("sources.manager_wakatime.EM") as mock_em:
            mock_em.WAKATIME_API_KEY = "test_api_key_123"
            assert WakaTimeManager.get_api_key() == "test_api_key_123"

    def test_get_api_key_returns_none_when_not_set(self):
        """Should return None when API key is not set."""
        with patch("sources.manager_wakatime.EM") as mock_em:
            mock_em.WAKATIME_API_KEY = None
            assert WakaTimeManager.get_api_key() is None

    def test_get_api_key_returns_none_for_empty_string(self):
        """Should return None when API key is empty string."""
        with patch("sources.manager_wakatime.EM") as mock_em:
            mock_em.WAKATIME_API_KEY = ""
            assert WakaTimeManager.get_api_key() is None


class TestWakaTimeManagerShowFlags:
    """Test suite for WakaTimeManager display flag retrieval."""

    def test_get_show_flags_returns_all_flags(self):
        """Should return dictionary with all show flags."""
        with patch("sources.manager_wakatime.EM") as mock_em:
            mock_em.SHOW_LANGUAGE = True
            mock_em.SHOW_EDITORS = False
            mock_em.SHOW_PROJECTS = True
            mock_em.SHOW_OS = False

            flags = WakaTimeManager.get_show_flags()

            assert flags == {
                "show_language": True,
                "show_editors": False,
                "show_projects": True,
                "show_os": False,
            }

    def test_get_show_flags_all_true(self):
        """Should handle all flags being True."""
        with patch("sources.manager_wakatime.EM") as mock_em:
            mock_em.SHOW_LANGUAGE = True
            mock_em.SHOW_EDITORS = True
            mock_em.SHOW_PROJECTS = True
            mock_em.SHOW_OS = True

            flags = WakaTimeManager.get_show_flags()

            assert all(flags.values())

    def test_get_show_flags_all_false(self):
        """Should handle all flags being False."""
        with patch("sources.manager_wakatime.EM") as mock_em:
            mock_em.SHOW_LANGUAGE = False
            mock_em.SHOW_EDITORS = False
            mock_em.SHOW_PROJECTS = False
            mock_em.SHOW_OS = False

            flags = WakaTimeManager.get_show_flags()

            assert not any(flags.values())


class TestWakaTimeManagerFetchStats:
    """Test suite for WakaTimeManager.fetch_stats() method."""

    @pytest.mark.asyncio
    async def test_fetch_stats_returns_none_when_not_configured(self):
        """Should return None when WakaTime is not configured."""
        with patch("sources.manager_wakatime.EM") as mock_em:
            mock_em.WAKATIME_API_KEY = None
            mock_em.SHOW_WAKATIME = False

            result = await WakaTimeManager.fetch_stats()
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_stats_returns_none_when_api_key_missing(self):
        """Should return None when API key is missing."""
        with patch("sources.manager_wakatime.EM") as mock_em:
            mock_em.WAKATIME_API_KEY = None
            mock_em.SHOW_WAKATIME = True

            result = await WakaTimeManager.fetch_stats()
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_stats_returns_data_on_success(self):
        """Should return stats data on successful API call."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "languages": [{"name": "Python", "percent": 50.0}],
                "editors": [{"name": "VS Code", "percent": 100.0}],
            }
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("sources.manager_wakatime.EM") as mock_em, \
             patch.object(WakaTimeManager, "_CLIENT", mock_client), \
             patch.object(WakaTimeManager, "init", new_callable=AsyncMock):
            mock_em.WAKATIME_API_KEY = "test_key"
            mock_em.SHOW_WAKATIME = True

            result = await WakaTimeManager.fetch_stats()

            assert result == {
                "languages": [{"name": "Python", "percent": 50.0}],
                "editors": [{"name": "VS Code", "percent": 100.0}],
            }
            from base64 import b64encode
            expected_token = b64encode(b"test_key:").decode()
            mock_client.get.assert_called_once_with(
                WAKATIME_ENDPOINTS["stats_last_7_days"],
                headers={"Authorization": f"Basic {expected_token}"},
            )

    @pytest.mark.asyncio
    async def test_fetch_stats_returns_none_on_401(self):
        """Should return None and log warning on 401 (invalid/expired key)."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("sources.manager_wakatime.EM") as mock_em, \
             patch.object(WakaTimeManager, "_CLIENT", mock_client), \
             patch.object(WakaTimeManager, "init", new_callable=AsyncMock), \
             patch("sources.manager_wakatime.DBM") as mock_dbm:
            mock_em.WAKATIME_API_KEY = "invalid_key"
            mock_em.SHOW_WAKATIME = True

            result = await WakaTimeManager.fetch_stats()

            assert result is None
            mock_dbm.w.assert_called_with("WakaTime API key is invalid or expired")

    @pytest.mark.asyncio
    async def test_fetch_stats_returns_none_on_402(self):
        """Should return None and log warning on 402 (paid plan required)."""
        mock_response = MagicMock()
        mock_response.status_code = 402

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("sources.manager_wakatime.EM") as mock_em, \
             patch.object(WakaTimeManager, "_CLIENT", mock_client), \
             patch.object(WakaTimeManager, "init", new_callable=AsyncMock), \
             patch("sources.manager_wakatime.DBM") as mock_dbm:
            mock_em.WAKATIME_API_KEY = "free_tier_key"
            mock_em.SHOW_WAKATIME = True

            result = await WakaTimeManager.fetch_stats()

            assert result is None
            mock_dbm.w.assert_called_with("WakaTime API requires a paid plan for this feature")

    @pytest.mark.asyncio
    async def test_fetch_stats_returns_none_on_other_error_codes(self):
        """Should return None and log warning on other non-200 status codes."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("sources.manager_wakatime.EM") as mock_em, \
             patch.object(WakaTimeManager, "_CLIENT", mock_client), \
             patch.object(WakaTimeManager, "init", new_callable=AsyncMock), \
             patch("sources.manager_wakatime.DBM") as mock_dbm:
            mock_em.WAKATIME_API_KEY = "test_key"
            mock_em.SHOW_WAKATIME = True

            result = await WakaTimeManager.fetch_stats()

            assert result is None
            mock_dbm.w.assert_called_with("WakaTime API returned status 500")

    @pytest.mark.asyncio
    async def test_fetch_stats_returns_none_when_data_field_missing(self):
        """Should return None when response is missing 'data' field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "something went wrong"}

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("sources.manager_wakatime.EM") as mock_em, \
             patch.object(WakaTimeManager, "_CLIENT", mock_client), \
             patch.object(WakaTimeManager, "init", new_callable=AsyncMock), \
             patch("sources.manager_wakatime.DBM") as mock_dbm:
            mock_em.WAKATIME_API_KEY = "test_key"
            mock_em.SHOW_WAKATIME = True

            result = await WakaTimeManager.fetch_stats()

            assert result is None
            mock_dbm.w.assert_called_with("WakaTime response missing 'data' field")

    @pytest.mark.asyncio
    async def test_fetch_stats_handles_request_error(self):
        """Should handle RequestError gracefully."""
        from httpx import RequestError

        mock_client = AsyncMock()
        mock_client.get.side_effect = RequestError("Connection failed")

        with patch("sources.manager_wakatime.EM") as mock_em, \
             patch.object(WakaTimeManager, "_CLIENT", mock_client), \
             patch.object(WakaTimeManager, "init", new_callable=AsyncMock), \
             patch("sources.manager_wakatime.DBM") as mock_dbm:
            mock_em.WAKATIME_API_KEY = "test_key"
            mock_em.SHOW_WAKATIME = True

            result = await WakaTimeManager.fetch_stats()

            assert result is None
            assert mock_dbm.w.called

    @pytest.mark.asyncio
    async def test_fetch_stats_handles_json_decode_error(self):
        """Should handle JSONDecodeError gracefully."""
        from json import JSONDecodeError

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        with patch("sources.manager_wakatime.EM") as mock_em, \
             patch.object(WakaTimeManager, "_CLIENT", mock_client), \
             patch.object(WakaTimeManager, "init", new_callable=AsyncMock), \
             patch("sources.manager_wakatime.DBM") as mock_dbm:
            mock_em.WAKATIME_API_KEY = "test_key"
            mock_em.SHOW_WAKATIME = True

            result = await WakaTimeManager.fetch_stats()

            assert result is None
            assert mock_dbm.w.called


class TestWakaTimeManagerClientManagement:
    """Test suite for WakaTimeManager client initialization and cleanup."""

    @pytest.mark.asyncio
    async def test_init_creates_client(self):
        """Should create AsyncClient on init."""
        # Reset client state
        WakaTimeManager._CLIENT = None

        with patch("sources.manager_wakatime.AsyncClient") as mock_client_class, \
             patch("sources.manager_wakatime.DBM"):
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            await WakaTimeManager.init()

            mock_client_class.assert_called_once_with(timeout=30.0)
            assert WakaTimeManager._CLIENT == mock_client

        # Cleanup
        WakaTimeManager._CLIENT = None

    @pytest.mark.asyncio
    async def test_init_does_not_recreate_client(self):
        """Should not recreate client if already initialized."""
        existing_client = MagicMock()
        WakaTimeManager._CLIENT = existing_client

        with patch("sources.manager_wakatime.AsyncClient") as mock_client_class:
            await WakaTimeManager.init()

            mock_client_class.assert_not_called()
            assert WakaTimeManager._CLIENT == existing_client

        # Cleanup
        WakaTimeManager._CLIENT = None

    @pytest.mark.asyncio
    async def test_close_closes_client(self):
        """Should close and clear client on close."""
        mock_client = AsyncMock()
        WakaTimeManager._CLIENT = mock_client

        await WakaTimeManager.close()

        mock_client.aclose.assert_called_once()
        assert WakaTimeManager._CLIENT is None

    @pytest.mark.asyncio
    async def test_close_handles_no_client(self):
        """Should handle close when no client exists."""
        WakaTimeManager._CLIENT = None

        # Should not raise
        await WakaTimeManager.close()

        assert WakaTimeManager._CLIENT is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

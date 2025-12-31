"""
WakaTime Manager - Handles WakaTime API integration.

This module provides functionality to fetch and process WakaTime statistics
for displaying coding activity in GitHub profile READMEs.
"""

from base64 import b64encode
from json import JSONDecodeError

from httpx import AsyncClient, RequestError

from .manager_environment import EnvironmentManager as EM
from .manager_debug import DebugManager as DBM


# WakaTime API endpoints
WAKATIME_API_BASE = "https://wakatime.com/api/v1"
WAKATIME_ENDPOINTS = {
    "stats_last_7_days": f"{WAKATIME_API_BASE}/users/current/stats/last_7_days",
}


class WakaTimeManager:
    """Manager class for WakaTime API interactions."""

    _CLIENT: AsyncClient | None = None

    @classmethod
    def is_configured(cls) -> bool:
        """
        Check if WakaTime integration is properly configured.

        Returns:
            True if WAKATIME_API_KEY is set and SHOW_WAKATIME is enabled.
        """
        return bool(EM.WAKATIME_API_KEY) and EM.SHOW_WAKATIME

    @classmethod
    def get_api_key(cls) -> str | None:
        """
        Get the WakaTime API key from environment.

        Returns:
            The API key or None if not set.
        """
        return EM.WAKATIME_API_KEY if EM.WAKATIME_API_KEY else None

    @classmethod
    async def init(cls) -> None:
        """Initialize the WakaTime HTTP client."""
        if cls._CLIENT is None:
            cls._CLIENT = AsyncClient(timeout=30.0)
            DBM.g("WakaTime manager initialized!")

    @classmethod
    async def close(cls) -> None:
        """Close the WakaTime HTTP client."""
        if cls._CLIENT:
            await cls._CLIENT.aclose()
            cls._CLIENT = None

    @classmethod
    async def fetch_stats(cls) -> dict | None:
        """
        Fetch WakaTime statistics for the last 7 days.

        Returns:
            Dictionary containing WakaTime stats data, or None if fetch fails.
        """
        if not cls.is_configured():
            DBM.i("WakaTime not configured, skipping stats fetch")
            return None

        api_key = cls.get_api_key()
        if not api_key:
            DBM.w("WakaTime API key not found")
            return None

        await cls.init()

        try:
            url = WAKATIME_ENDPOINTS["stats_last_7_days"]
            DBM.i("Fetching WakaTime stats...")

            auth_token = b64encode(f"{api_key}:".encode()).decode()
            response = await cls._CLIENT.get(
                url,
                headers={"Authorization": f"Basic {auth_token}"},
            )

            if response.status_code == 401:
                DBM.w("WakaTime API key is invalid or expired")
                return None

            if response.status_code == 402:
                DBM.w("WakaTime API requires a paid plan for this feature")
                return None

            if response.status_code != 200:
                DBM.w(f"WakaTime API returned status {response.status_code}")
                return None

            data = response.json()

            if "data" not in data:
                DBM.w("WakaTime response missing 'data' field")
                return None

            DBM.g("WakaTime stats fetched successfully!")
            return data["data"]

        except (RequestError, JSONDecodeError) as e:
            DBM.w(f"Failed to fetch WakaTime stats: {e!r}")
            return None

    @classmethod
    def get_show_flags(cls) -> dict[str, bool]:
        """
        Get the current WakaTime display flags.

        Returns:
            Dictionary with show flags for each WakaTime feature.
        """
        return {
            "show_language": EM.SHOW_LANGUAGE,
            "show_editors": EM.SHOW_EDITORS,
            "show_projects": EM.SHOW_PROJECTS,
            "show_os": EM.SHOW_OS,
        }

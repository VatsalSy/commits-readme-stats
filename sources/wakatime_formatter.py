"""
WakaTime Formatter - Formats WakaTime statistics for README display.

This module provides formatting functions to convert WakaTime API data
into markdown-formatted text with progress bars for GitHub profile READMEs.
"""

from typing import Dict, List, Optional

from .graphics_list_formatter import make_list
from .manager_file import FileManager as FM


# Section labels for WakaTime stats
WAKATIME_SECTIONS = {
    "languages": "💬 Programming Languages",
    "editors": "🔥 Editors",
    "projects": "🐱‍💻 Projects",
    "operating_systems": "💻 Operating System",
}


def _filter_and_renormalize_other(data: List[Dict]) -> List[Dict]:
    """
    Filter out "Other" entries and renormalize percentages.

    Removes all entries where name.lower() == "other" and recalculates
    percentages so remaining entries sum to 100%.

    Args:
        data: List of WakaTime data items with name and percent keys

    Returns:
        Filtered and renormalized list of data items

    Edge cases handled:
        - Empty list: returns empty list
        - All "Other" entries: returns empty list
        - No "Other" entries: returns original data with adjusted decimals
        - Zero sum: returns empty list (defensive programming)
    """
    if not data:
        return []

    # Filter out "Other" entries (case-insensitive)
    filtered_data = [
        item for item in data
        if item.get("name", "").lower() != "other"
    ]

    # If no items remain, return empty list
    if not filtered_data:
        return []

    # Calculate sum of remaining percentages
    percent_sum = sum(item.get("percent", 0.0) for item in filtered_data)

    # Handle edge case: zero sum (defensive programming)
    if percent_sum <= 0:
        return []

    # Renormalize percentages to sum to 100%
    for item in filtered_data:
        old_percent = item.get("percent", 0.0)
        new_percent = (old_percent / percent_sum) * 100.0
        item["percent"] = round(new_percent, 2)

    return filtered_data


def _format_section(
    title: str,
    data: List[Dict],
    top_num: int = 5
) -> str:
    """
    Format a single WakaTime stats section.

    Args:
        title: Section title (e.g., "Programming Languages")
        data: List of WakaTime data items with name, text, percent keys
        top_num: Number of items to display

    Returns:
        Formatted markdown string for the section
    """
    if not data:
        return ""

    # Extract data in the format expected by make_list
    formatted_data = []
    for item in data[:top_num]:
        formatted_data.append({
            "name": item.get("name", "Unknown"),
            "text": item.get("text", "0 mins"),
            "percent": item.get("percent", 0.0)
        })

    if not formatted_data:
        return ""

    section = f"{title}\n"
    section += make_list(data=formatted_data, top_num=top_num, sort=False)
    section += "\n\n"
    return section


def format_wakatime_stats(
    data: Dict,
    show_flags: Dict[str, bool]
) -> str:
    """
    Format WakaTime statistics into markdown.

    Args:
        data: WakaTime API response data
        show_flags: Dictionary of flags indicating which sections to show

    Returns:
        Formatted markdown string containing WakaTime stats
    """
    if not data:
        return ""

    stats = "**This Week I Spent My Time On** \n\n```text\n"

    # Programming Languages
    if show_flags.get("show_language", True):
        languages = _filter_and_renormalize_other(data.get("languages", []))
        if languages:
            stats += _format_section(
                WAKATIME_SECTIONS["languages"],
                languages,
                top_num=5
            )

    # Editors
    if show_flags.get("show_editors", True):
        editors = _filter_and_renormalize_other(data.get("editors", []))
        if editors:
            stats += _format_section(
                WAKATIME_SECTIONS["editors"],
                editors,
                top_num=5
            )

    # Projects
    if show_flags.get("show_projects", True):
        projects = _filter_and_renormalize_other(data.get("projects", []))
        if projects:
            stats += _format_section(
                WAKATIME_SECTIONS["projects"],
                projects,
                top_num=5
            )

    # Operating System
    if show_flags.get("show_os", True):
        operating_systems = _filter_and_renormalize_other(data.get("operating_systems", []))
        if operating_systems:
            stats += _format_section(
                WAKATIME_SECTIONS["operating_systems"],
                operating_systems,
                top_num=5
            )

    stats += "```\n"

    return stats


def format_no_activity() -> str:
    """
    Return a placeholder message when no WakaTime activity is found.

    Returns:
        Markdown string indicating no activity
    """
    return "**This Week I Spent My Time On** \n\n```text\nNo Activity Tracked This Week\n```\n"

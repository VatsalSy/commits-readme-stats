"""
WakaTime Formatter - Formats WakaTime statistics for README display.

This module provides formatting functions to convert WakaTime API data
into markdown-formatted text with progress bars for GitHub profile READMEs.
"""

from .graphics_list_formatter import make_list


# Section labels for WakaTime stats
WAKATIME_SECTIONS = {
    "languages": "💬 Programming Languages",
    "editors": "🔥 Editors",
    "projects": "🐱‍💻 Projects",
    "operating_systems": "💻 Operating System",
}


def _filter_and_renormalize_other(data: list[dict]) -> list[dict]:
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
    # Use .copy() to avoid mutating original data
    filtered_data = [
        item.copy() for item in data
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
    renormalized = [
        (item.get("percent", 0.0) / percent_sum) * 100.0
        for item in filtered_data
    ]

    # Use integer centi-percent units (0.01%) to keep sum at 100.00 without
    # forcing a potentially negative correction into a single bucket.
    scaled_units = [value * 100 for value in renormalized]
    base_units = [int(value) for value in scaled_units]
    remaining_units = 10000 - sum(base_units)
    if remaining_units > 0:
        order = sorted(
            range(len(scaled_units)),
            key=lambda i: (scaled_units[i] - base_units[i], renormalized[i], -i),
            reverse=True,
        )
        for offset in range(remaining_units):
            base_units[order[offset % len(order)]] += 1

    rounded = [value / 100.0 for value in base_units]

    for index, item in enumerate(filtered_data):
        item["percent"] = rounded[index]

    return filtered_data


def _format_section(
    title: str,
    data: list[dict],
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
    data: dict,
    show_flags: dict[str, bool]
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

    # Check if any sections were added (stats only has header if empty)
    header_only = "**This Week I Spent My Time On** \n\n```text\n"
    if stats == header_only:
        return format_no_activity()

    stats += "```\n"

    return stats


def format_no_activity() -> str:
    """
    Return a placeholder message when no WakaTime activity is found.

    Returns:
        Markdown string indicating no activity
    """
    return "**This Week I Spent My Time On** \n\n```text\nNo Activity Tracked This Week\n```\n"

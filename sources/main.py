"""
Readme Development Metrics With waka time progress
"""
from asyncio import run
from datetime import datetime
from typing import Dict

from manager_download import init_download_manager, DownloadManager as DM
from manager_environment import EnvironmentManager as EM
from manager_github import init_github_manager, GitHubManager as GHM
from manager_file import init_localization_manager, FileManager as FM
from manager_debug import init_debug_manager, DebugManager as DBM
from yearly_commit_calculator import calculate_commit_data
from graphics_list_formatter import make_commit_day_time_list


async def get_stats() -> str:
    """
    Creates new README.md content with commit statistics.
    """
    DBM.i("Collecting commit stats for README...")

    stats = str()
    repositories = await collect_user_repositories()

    if EM.SHOW_COMMIT or EM.SHOW_DAYS_OF_WEEK:
        yearly_data, commit_data = await calculate_commit_data(repositories)
        timezone = "UTC"  # Default to UTC since we don't need WakaTime for timezone
        DBM.i("Adding user commit day time info...")
        stats += f"{await make_commit_day_time_list(timezone, repositories, commit_data)}\n\n"

    DBM.g("Stats for README collected!")
    return stats


async def main():
    """
    Application main function.
    Initializes managers, collects commit info and updates README.md.
    """
    init_github_manager()
    await init_download_manager(GHM.USER.login)
    init_localization_manager()
    DBM.i("Managers initialized.")

    stats = await get_stats()
    if not EM.DEBUG_RUN:
        GHM.update_readme(stats)
        GHM.commit_update()
    else:
        GHM.set_github_output(stats)
    await DM.close_remote_resources()


if __name__ == "__main__":
    init_debug_manager()
    start_time = datetime.now()
    DBM.g("Program execution started at $date.", date=start_time)
    run(main())
    end_time = datetime.now()
    DBM.g("Program execution finished at $date.", date=end_time)
    DBM.p("Program finished in $time.", time=end_time - start_time)

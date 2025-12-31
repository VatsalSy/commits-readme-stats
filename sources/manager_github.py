from base64 import b64encode
import os
from os import environ, makedirs, path
from os.path import dirname, join
from random import choice
import re
from shutil import copy, rmtree
from string import ascii_letters

from git import Repo, Actor
from github import Github, AuthenticatedUser, Repository

from .manager_environment import EnvironmentManager as EM
from .manager_file import FileManager as FM
from .manager_debug import DebugManager as DBM
from .manager_token import TokenManager


def init_github_manager():
    """
    Initialize GitHub manager.
    Current user, user readme repo and readme file are downloaded.
    """
    GitHubManager.prepare_github_env()
    DBM.i(f"Authenticated as: {GitHubManager.USER.login}")


class GitHubManager:
    USER: AuthenticatedUser
    REPO: Repo
    REMOTE: Repository

    _REMOTE_NAME: str
    _REMOTE_PATH: str
    _SINGLE_COMMIT_BRANCH = "latest_branch"

    _START_COMMENT = f"<!--START_SECTION:{EM.SECTION_NAME}-->"
    _END_COMMENT = f"<!--END_SECTION:{EM.SECTION_NAME}-->"
    _README_REGEX = f"{_START_COMMENT}[\\s\\S]+{_END_COMMENT}"

    @staticmethod
    def prepare_github_env():
        """
        Download and store for future use:
        - Current GitHub user.
        - Named repo of the user [username]/[username].
        - Clone of the named repo.
        """
        try:
            github = Github(EM.GH_COMMIT_TOKEN)
            clone_path = "repo"
            GitHubManager.USER = github.get_user()
            rmtree(clone_path, ignore_errors=True)

            GitHubManager._REMOTE_NAME = f"{GitHubManager.USER.login}/{GitHubManager.USER.login}"
            repo_url = f"https://github.com/{GitHubManager._REMOTE_NAME}.git"
            
            # Use secure credential helper instead of token in URL
            credentials = TokenManager.get_credentials_helper()
            DBM.i(f"Cloning from: {repo_url}")
            
            # Clone using credential helper environment
            GitHubManager.REMOTE = github.get_repo(GitHubManager._REMOTE_NAME)
            GitHubManager.REPO = Repo.clone_from(
                repo_url, 
                to_path=clone_path,
                env=credentials
            )
            
            DBM.g("Repository cloned successfully")
            
        except Exception as e:
            error_msg = TokenManager.mask_token(str(e))
            DBM.p(f"Error preparing GitHub environment: {error_msg}")
            raise

    @staticmethod
    def _get_author() -> Actor:
        """
        Gets GitHub commit author specified by environmental variables.
        It is the user himself or a 'readme-bot'.

        :returns: Commit author.
        """
        if EM.COMMIT_BY_ME:
            return Actor(EM.COMMIT_USERNAME or GitHubManager.USER.login, EM.COMMIT_EMAIL or GitHubManager.USER.email)
        else:
            return Actor(EM.COMMIT_USERNAME or "readme-bot", EM.COMMIT_EMAIL or "41898282+github-actions[bot]@users.noreply.github.com")

    @staticmethod
    def branch(requested_branch: str) -> str:
        """
        Gets requested branch name or the default branch name if requested branch wasn't found.
        The default branch name is regularly, 'main' or 'master'.

        :param requested_branch: Requested branch name.
        :returns: Commit author.
        """
        return GitHubManager.REMOTE.default_branch if requested_branch == "" else requested_branch

    @staticmethod
    def _copy_file_and_add_to_repo(src_path: str):
        """
        Copies file to repository folder, creating path if needed and adds file to git.
        The copied file relative to repository root path will be equal the source file relative to work directory path.

        :param src_path: Source file path.
        """
        dst_path = join(GitHubManager.REPO.working_tree_dir, src_path)
        makedirs(dirname(dst_path), exist_ok=True)
        copy(src_path, dst_path)
        GitHubManager.REPO.git.add(dst_path)

    @staticmethod
    def update_readme(stats: str, section_name: str | None = None) -> None:
        """
        Updates README.md content between section markers with new stats.

        Args:
            stats: The formatted statistics string to insert.
            section_name: Optional section name for markers. Defaults to EM.SECTION_NAME.
                         Use "wakatime" for WakaTime stats section.
        """
        readme_path = "repo/README.md"

        # Use provided section name or default
        section = section_name if section_name else EM.SECTION_NAME

        try:
            # Read current README content
            with open(readme_path, encoding="utf-8") as f:
                content = f.read()

            # Build markers for the specified section
            start_marker = f"<!--START_SECTION:{section}-->"
            end_marker = f"<!--END_SECTION:{section}-->"
            section_regex = f"{start_marker}[\\s\\S]+{end_marker}"

            # Create new content with stats
            new_content = f"{start_marker}\n{stats}{end_marker}"

            # Replace old section with new content
            if re.search(section_regex, content):
                updated_content = re.sub(
                    section_regex,
                    new_content,
                    content
                )
                DBM.g(f"README.md section '{section}' updated successfully!")
            else:
                # If markers don't exist, don't append - just log a warning
                DBM.w(f"Section markers for '{section}' not found in README.md. Skipping update.")
                DBM.i("Add these markers to your README.md to enable this section:")
                DBM.i(f"  {start_marker}")
                DBM.i(f"  {end_marker}")
                return

            # Write updated content back to README
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

        except (OSError, re.error) as e:
            DBM.p(f"Error updating README section '{section}': {type(e).__name__}: {e!s}")

    @staticmethod
    def update_chart(name: str, path: str) -> str:
        """
        Updates a chart.
        Inlines data into readme if in debug mode, commits otherwise.
        Uses commit author, commit message and branch name specified by environmental variables.

        :param name: Name of the chart to update.
        :param path: Path of the chart to update.
        :returns: String to add to README file.
        """
        output = str()
        DBM.i(f"Updating {name} chart...")
        if not EM.DEBUG_RUN:
            DBM.i("\tAdding chart to repo...")
            GitHubManager._copy_file_and_add_to_repo(path)
            chart_path = f"https://raw.githubusercontent.com/{GitHubManager._REMOTE_NAME}/{GitHubManager.branch(EM.PUSH_BRANCH_NAME)}/{path}"
            output += f"![{name} chart]({chart_path})\n\n"

        else:
            DBM.i("\tInlining chart...")
            hint = "You can use [this website](https://codebeautify.org/base64-to-image-converter) to view the generated base64 image."
            with open(path, "rb") as input_file:
                output += f"{hint}\n```\ndata:image/png;base64,{b64encode(input_file.read()).decode('utf-8')}\n```\n\n"
        return output

    @staticmethod
    def commit_update():
        """
        Commit update data to repository.
        """
        try:
            # Use secure credential helper instead of token in URL
            credentials = TokenManager.get_credentials_helper()
            DBM.i(f"Setting up Git credentials for: {GitHubManager._REMOTE_NAME}")
            
            # Configure git environment with credentials
            GitHubManager.REPO.git.update_environment(**credentials)
            
            # Add the README file to git
            DBM.i("Adding README.md to git index...")
            GitHubManager.REPO.index.add(['README.md'])
            
            actor = GitHubManager._get_author()
            DBM.i(f"Committing as: {actor.name} <{actor.email}>")
            GitHubManager.REPO.index.commit(EM.COMMIT_MESSAGE, author=actor, committer=actor)

            if EM.COMMIT_SINGLE:
                DBM.i("Pushing files to repo as a single commit...")
                refspec = f"{GitHubManager._SINGLE_COMMIT_BRANCH}:{GitHubManager.branch(EM.PUSH_BRANCH_NAME)}"
                DBM.i(f"Using refspec: {refspec}")
                headers = GitHubManager.REPO.remotes.origin.push(force=True, refspec=refspec)
            else:
                DBM.i("Pushing files to repo...")
                current_branch = GitHubManager.REPO.active_branch.name
                DBM.i(f"Pushing current branch: {current_branch}")
                headers = GitHubManager.REPO.remotes.origin.push()

            if len(headers) == 0:
                raise Exception("Push failed - no headers returned")
            else:
                DBM.i(f"Push response: {headers}")
                DBM.g("Repository synchronized!")

        except Exception as e:
            # Safely log error without exposing sensitive data
            error_msg = TokenManager.mask_token(str(e))
            DBM.p(f"Error in commit update: {error_msg}")
            raise

    @staticmethod
    def set_github_output(stats: str):
        """
        Output readme data as current action output instead of committing it.

        :param stats: String representation of stats to output.
        """
        DBM.i("Setting README contents as action output...")
        if "GITHUB_OUTPUT" not in environ.keys():
            DBM.p("Not in GitHub environment, not setting action output!")
            return
        else:
            DBM.i("Outputting readme contents, check the latest comment for the generated stats.")

        prefix = "README stats current output:"
        eol = "".join(choice(ascii_letters) for _ in range(10))
        FM.write_file(environ["GITHUB_OUTPUT"], f"README_CONTENT<<{eol}\n{prefix}\n\n{stats}\n{eol}\n", append=True)

        DBM.g("Action output set!")

    @staticmethod
    async def user_exists(username: str) -> bool:
        """Check if a GitHub user exists."""
        try:
            github = Github(EM.GH_COMMIT_TOKEN)
            user = github.get_user(username)
            # Try to access a property to verify the user exists
            _ = user.login
            return True
        except Exception as e:
            DBM.i(f"Error checking user existence: {str(e)}")
            return False

    @staticmethod
    def init_repo():
        """Initialize repository connection"""
        GitHubManager._REMOTE_NAME = f"{GitHubManager.USER.login}/{GitHubManager.USER.login}"
        # Use HTTPS URL without credentials
        GitHubManager._REPO_PATH = f"https://github.com/{GitHubManager._REMOTE_NAME}.git"
        
        try:
            # If repo directory exists, remove it
            if os.path.exists("repo"):
                rmtree("repo")
                
            # Get credentials using the secure helper
            credentials = TokenManager.get_credentials_helper()
            
            # Clone using GitPython with secure credential handling
            Repo.clone_from(
                GitHubManager._REPO_PATH,
                "repo",
                env=credentials
            )
            DBM.g("Repository cloned successfully")
            
        except Exception as e:
            error_msg = TokenManager.mask_token(str(e))
            DBM.p(f"Error cloning repository: {error_msg}")
            raise

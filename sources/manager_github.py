from base64 import b64encode
from os import environ, makedirs
from os.path import dirname, join
from random import choice
from re import sub
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
            github = Github(EM.GH_TOKEN)
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
    def update_readme(stats: str) -> None:
        """
        Updates README.md content between section markers with new stats.
        """
        readme_path = "repo/README.md"
        
        try:
            # Read current README content
            with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace content between markers
            start_marker = GitHubManager._START_COMMENT
            end_marker = GitHubManager._END_COMMENT
            
            # Create new content with stats
            new_content = f"{start_marker}\n{stats}{end_marker}"
            
            # Replace old section with new content
            import re
            if re.search(GitHubManager._README_REGEX, content):
                updated_content = re.sub(
                    GitHubManager._README_REGEX,
                    new_content,
                    content
                )
            else:
                # If markers don't exist, append to end
                updated_content = f"{content}\n{new_content}"
                
            # Write updated content back to README
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
                
            DBM.g("README.md updated successfully!")
            
        except Exception as e:
            DBM.p(f"Error updating README: {str(e)}")

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
        actor = GitHubManager._get_author()
        DBM.i("Committing files to repo...")
        GitHubManager.REPO.index.commit(EM.COMMIT_MESSAGE, author=actor, committer=actor)

        if EM.COMMIT_SINGLE:
            DBM.i("Pushing files to repo as a single commit...")
            refspec = f"{GitHubManager._SINGLE_COMMIT_BRANCH}:{GitHubManager.branch(EM.PUSH_BRANCH_NAME)}"
            headers = GitHubManager.REPO.remotes.origin.push(force=True, refspec=refspec)
        else:
            DBM.i("Pushing files to repo...")
            headers = GitHubManager.REPO.remotes.origin.push()

        if len(headers) == 0:
            DBM.i(f"Repository push error: {headers}!")
        else:
            DBM.i("Repository synchronized!")

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
            github = Github(EM.GH_TOKEN)
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
                
            # Clone using GitPython with credentials configured via environment
            from git import Repo
            git_env = os.environ.copy()
            # Configure git to use token via environment
            git_env["GIT_ASKPASS"] = "echo"
            git_env["GIT_USERNAME"] = GitHubManager.USER.login
            git_env["GIT_PASSWORD"] = EM.GH_TOKEN
            
            Repo.clone_from(
                GitHubManager._REPO_PATH,
                "repo",
                env=git_env
            )
            DBM.g("Repository cloned successfully")
            
        except Exception as e:
            DBM.p(f"Error cloning repository: {str(e)}")
            raise

from os import getenv, environ
from .manager_base import BaseEnvironmentManager
from .manager_token import TokenManager
from .manager_config import Configuration


class EnvironmentManager(BaseEnvironmentManager):
    """Class for handling environmental variables"""

    GH_COMMIT_TOKEN: str = None  # Will be set during initialization

    SECTION_NAME = getenv("INPUT_SECTION_NAME", "github-stats")
    PULL_BRANCH_NAME = getenv("INPUT_PULL_BRANCH_NAME", "")
    PUSH_BRANCH_NAME = getenv("INPUT_PUSH_BRANCH_NAME", "")

    SHOW_COMMIT = BaseEnvironmentManager.is_truthy(getenv("INPUT_SHOW_COMMIT", "True"))
    SHOW_DAYS_OF_WEEK = BaseEnvironmentManager.is_truthy(getenv("INPUT_SHOW_DAYS_OF_WEEK", "True"))

    COMMIT_BY_ME = BaseEnvironmentManager.is_truthy(getenv("INPUT_COMMIT_BY_ME", "False"))
    COMMIT_MESSAGE = getenv("INPUT_COMMIT_MESSAGE", "Updated with Dev Metrics")
    COMMIT_USERNAME = getenv("INPUT_COMMIT_USERNAME", "")
    COMMIT_EMAIL = getenv("INPUT_COMMIT_EMAIL", "")
    COMMIT_SINGLE = BaseEnvironmentManager.is_truthy(getenv("INPUT_COMMIT_SINGLE", ""))

    LOCALE = getenv("INPUT_LOCALE", "en")
    DEBUG_LOGGING = BaseEnvironmentManager.is_truthy(getenv("INPUT_DEBUG_LOGGING", "0"))
    DEBUG_RUN = BaseEnvironmentManager.is_truthy(getenv("DEBUG_RUN", "False"))
    USERNAME = getenv("INPUT_USERNAME", "")

    SYMBOL_VERSION = getenv("INPUT_SYMBOL_VERSION", "1")

    IGNORED_REPOS = [r.strip() for r in getenv("INPUT_IGNORED_REPOS", "").split(",") if r.strip()]

    @classmethod
    def init(cls):
        """Initialize environment manager"""
        cls.GH_COMMIT_TOKEN = TokenManager.get_token()

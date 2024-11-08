from os import getenv, environ
from .manager_base import BaseEnvironmentManager
from .manager_token import TokenManager
from .manager_config import Configuration


class EnvironmentManager(BaseEnvironmentManager):
    """Class for handling environmental variables"""

    GH_TOKEN: str = None  # Will be set during initialization

    SECTION_NAME = getenv("INPUT_SECTION_NAME", "github-stats")
    PULL_BRANCH_NAME = getenv("INPUT_PULL_BRANCH_NAME", "")
    PUSH_BRANCH_NAME = getenv("INPUT_PUSH_BRANCH_NAME", "")

    SHOW_COMMIT = getenv("INPUT_SHOW_COMMIT", "True").lower() in BaseEnvironmentManager._TRUTHY
    SHOW_DAYS_OF_WEEK = getenv("INPUT_SHOW_DAYS_OF_WEEK", "True").lower() in BaseEnvironmentManager._TRUTHY

    COMMIT_BY_ME = getenv("INPUT_COMMIT_BY_ME", "False").lower() in BaseEnvironmentManager._TRUTHY
    COMMIT_MESSAGE = getenv("INPUT_COMMIT_MESSAGE", "Updated with Dev Metrics")
    COMMIT_USERNAME = getenv("INPUT_COMMIT_USERNAME", "")
    COMMIT_EMAIL = getenv("INPUT_COMMIT_EMAIL", "")
    COMMIT_SINGLE = getenv("INPUT_COMMIT_SINGLE", "").lower() in BaseEnvironmentManager._TRUTHY

    LOCALE = getenv("INPUT_LOCALE", "en")
    DEBUG_LOGGING = getenv("INPUT_DEBUG_LOGGING", "0").lower() in BaseEnvironmentManager._TRUTHY
    DEBUG_RUN = getenv("DEBUG_RUN", "False").lower() in BaseEnvironmentManager._TRUTHY
    USERNAME = getenv("INPUT_USERNAME", "")

    SYMBOL_VERSION = getenv("INPUT_SYMBOL_VERSION", "1")

    IGNORED_REPOS = [r.strip() for r in getenv("INPUT_IGNORED_REPOS", "").split(",") if r.strip()]

    @classmethod
    def init(cls):
        """Initialize environment manager"""
        cls.GH_TOKEN = TokenManager.get_token()

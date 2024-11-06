from os import getenv, environ


class EnvironmentManager:
    """
    Class for handling environmental variables used by the action.
    Only SHOW_COMMIT and SHOW_DAYS_OF_WEEK flags are kept.
    """

    _TRUTHY = ["true", "1", "t", "y", "yes"]

    GH_TOKEN = environ["INPUT_GH_TOKEN"]

    SECTION_NAME = getenv("INPUT_SECTION_NAME", "github-stats")
    PULL_BRANCH_NAME = getenv("INPUT_PULL_BRANCH_NAME", "")
    PUSH_BRANCH_NAME = getenv("INPUT_PUSH_BRANCH_NAME", "")

    SHOW_COMMIT = getenv("INPUT_SHOW_COMMIT", "True").lower() in _TRUTHY
    SHOW_DAYS_OF_WEEK = getenv("INPUT_SHOW_DAYS_OF_WEEK", "True").lower() in _TRUTHY

    COMMIT_BY_ME = getenv("INPUT_COMMIT_BY_ME", "False").lower() in _TRUTHY
    COMMIT_MESSAGE = getenv("INPUT_COMMIT_MESSAGE", "Updated with Dev Metrics")
    COMMIT_USERNAME = getenv("INPUT_COMMIT_USERNAME", "")
    COMMIT_EMAIL = getenv("INPUT_COMMIT_EMAIL", "")
    COMMIT_SINGLE = getenv("INPUT_COMMIT_SINGLE", "").lower() in _TRUTHY

    LOCALE = getenv("INPUT_LOCALE", "en")
    DEBUG_LOGGING = getenv("INPUT_DEBUG_LOGGING", "0").lower() in _TRUTHY
    DEBUG_RUN = getenv("DEBUG_RUN", "False").lower() in _TRUTHY

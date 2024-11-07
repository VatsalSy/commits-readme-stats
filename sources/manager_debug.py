from logging import getLogger, Logger, StreamHandler, INFO, DEBUG
from string import Template
from datetime import datetime
from humanize import precisedelta
from typing import Dict


class DebugManager:
    """Debug logging manager"""
    
    _COLOR_RESET = "\u001B[0m"
    _COLOR_RED = "\u001B[31m"
    _COLOR_GREEN = "\u001B[32m"
    _COLOR_BLUE = "\u001B[34m"
    _COLOR_YELLOW = "\u001B[33m"

    _DATE_TEMPLATE = "date"
    _TIME_TEMPLATE = "time"

    _logger: Logger

    @staticmethod
    def create_logger(level: str = "INFO"):
        """Create and configure logger"""
        DebugManager._logger = getLogger(__name__)
        DebugManager._logger.setLevel(DEBUG if level.upper() == "DEBUG" else INFO)
        
        # Add stream handler if none exists
        if not DebugManager._logger.handlers:
            handler = StreamHandler()
            DebugManager._logger.addHandler(handler)

    @staticmethod
    def _process_template(message: str, kwargs: Dict) -> str:
        if DebugManager._DATE_TEMPLATE in kwargs:
            kwargs[DebugManager._DATE_TEMPLATE] = f"{datetime.strftime(kwargs[DebugManager._DATE_TEMPLATE], '%d-%m-%Y %H:%M:%S:%f')}"
        if DebugManager._TIME_TEMPLATE in kwargs:
            kwargs[DebugManager._TIME_TEMPLATE] = precisedelta(kwargs[DebugManager._TIME_TEMPLATE], minimum_unit="microseconds")

        message = Template(message).substitute(kwargs)
        
        # Import TokenManager here to avoid circular import
        from .manager_token import TokenManager
        return TokenManager.mask_token(message)

    @staticmethod
    def g(message: str, **kwargs):
        """Log success message"""
        message = DebugManager._process_template(message, kwargs)
        DebugManager._logger.info(f"{DebugManager._COLOR_GREEN}{message}{DebugManager._COLOR_RESET}")

    @staticmethod
    def i(message: str, **kwargs):
        """Log info message"""
        message = DebugManager._process_template(message, kwargs)
        DebugManager._logger.debug(f"{DebugManager._COLOR_BLUE}{message}{DebugManager._COLOR_RESET}")

    @staticmethod
    def w(message: str, **kwargs):
        """Log warning message"""
        message = DebugManager._process_template(message, kwargs)
        DebugManager._logger.warning(f"{DebugManager._COLOR_YELLOW}{message}{DebugManager._COLOR_RESET}")

    @staticmethod
    def p(message: str, **kwargs):
        """Log error message"""
        message = DebugManager._process_template(message, kwargs)
        DebugManager._logger.error(f"{DebugManager._COLOR_RED}{message}{DebugManager._COLOR_RESET}")


def init_debug_manager():
    """Initialize debug manager with appropriate log level"""
    from .manager_environment import EnvironmentManager as EM
    level = "DEBUG" if EM.DEBUG_LOGGING else "INFO"
    DebugManager.create_logger(level)

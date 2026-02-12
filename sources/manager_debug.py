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

    _logger: Logger | None = None

    @staticmethod
    def _get_logger() -> Logger:
        """Return an initialized logger, creating a default one on demand."""
        if DebugManager._logger is None:
            DebugManager.create_logger("INFO")
        return DebugManager._logger

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
        DebugManager._get_logger().info(f"{DebugManager._COLOR_GREEN}{message}{DebugManager._COLOR_RESET}")

    @staticmethod
    def i(message: str, **kwargs):
        """Log info message"""
        message = DebugManager._process_template(message, kwargs)
        DebugManager._get_logger().debug(f"{DebugManager._COLOR_BLUE}{message}{DebugManager._COLOR_RESET}")

    @staticmethod
    def w(message: str, **kwargs):
        """Log warning message"""
        message = DebugManager._process_template(message, kwargs)
        DebugManager._get_logger().warning(f"{DebugManager._COLOR_YELLOW}{message}{DebugManager._COLOR_RESET}")

    @staticmethod
    def p(message: str, **kwargs):
        """Log error message"""
        message = DebugManager._process_template(message, kwargs)
        DebugManager._get_logger().error(f"{DebugManager._COLOR_RED}{message}{DebugManager._COLOR_RESET}")

    @staticmethod
    def handle_error(error: Exception, context: str = "", mask_token: bool = True) -> str:
        """
        Securely handle and format error messages
        
        :param error: The exception to handle
        :param context: Optional context about where the error occurred
        :param mask_token: Whether to mask sensitive tokens in the message
        :return: Sanitized error message
        """
        from .manager_environment import EnvironmentManager as EM
        from .manager_token import TokenManager
        
        # Get base error message
        error_msg = str(error)
        
        # Mask tokens if requested
        if mask_token:
            error_msg = TokenManager.mask_token(error_msg)
        
        # Create generic message for production
        if not EM.DEBUG_RUN:
            if "permission denied" in error_msg.lower():
                return "Access denied - please check your permissions"
            elif "authentication failed" in error_msg.lower():
                return "Authentication failed - please verify your credentials"
            elif "not found" in error_msg.lower():
                return "Requested resource not found"
            else:
                return "An error occurred processing your request"
        
        # Return detailed message for debug mode
        prefix = f"{context}: " if context else ""
        return f"{prefix}{error_msg}"


def init_debug_manager():
    """Initialize debug manager with appropriate log level"""
    from .manager_environment import EnvironmentManager as EM
    level = "DEBUG" if EM.DEBUG_LOGGING else "INFO"
    DebugManager.create_logger(level)

from os import getenv, environ
from typing import List, Union

class BaseEnvironmentManager:
    """Base class for environment variables"""
    
    _TRUTHY: List[str] = ["true", "1", "t", "y", "yes"]
    
    @staticmethod
    def is_truthy(value: Union[str, int, bool]) -> bool:
        """
        Check if a value should be considered truthy.
        
        Args:
            value: Input value that could be string, int, or bool
            
        Returns:
            bool: True if value is considered truthy
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            return value.lower() in BaseEnvironmentManager._TRUTHY
        return False

from os import getenv, environ
from typing import List

class BaseEnvironmentManager:
    """Base class for environment variables"""
    
    _TRUTHY: List[str] = ["true", "1", "t", "y", "yes"]
    
    @staticmethod
    def is_truthy(value: str) -> bool:
        return value.lower() in BaseEnvironmentManager._TRUTHY 
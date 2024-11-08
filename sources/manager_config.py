from dataclasses import dataclass
from typing import Optional
from .manager_debug import DebugManager as DBM

@dataclass
class Configuration:
    """Secure configuration management"""
    _debug: bool = False
    _username: Optional[str] = None
    
    @property
    def debug(self) -> bool:
        return self._debug
        
    @debug.setter 
    def debug(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError("Debug must be boolean")
        self._debug = value
        DBM.i(f"Debug mode set to: {value}")
        
    @property
    def username(self) -> Optional[str]:
        return self._username
        
    @username.setter
    def username(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Username cannot be empty")
        self._username = value.strip()
        DBM.i(f"Username set to: {value}")

    def to_env_dict(self) -> dict:
        """
        Convert configuration to environment variables dict
        Used for compatibility with existing code
        """
        return {
            "DEBUG_RUN": str(self._debug),
            "INPUT_USERNAME": self._username
        }

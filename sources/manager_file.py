from os.path import join, isfile, dirname, exists
from os import makedirs, chmod
from json import load as load_json
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet, InvalidToken
import stat
import io
import re
from functools import wraps
from time import sleep
import signal
from contextlib import contextmanager
import json
import os

from .manager_environment import EnvironmentManager as EM
from .manager_debug import DebugManager as DBM


def init_localization_manager():
    """
    Initialize localization manager.
    Load GUI translations JSON file.
    """
    FileManager.load_localization("translation.json")


class TimeoutException(Exception):
    pass


@contextmanager
def timeout(seconds):
    """Context manager for timing out operations"""
    def timeout_handler(signum, frame):
        raise TimeoutException("Operation timed out")

    # Set the timeout handler
    original_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Restore the original handler and disable alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)


class FileManager:
    """
    Class for handling localization (and maybe other file IO in future).
    Stores localization in dictionary.
    """

    ASSETS_DIR = "assets"
    _LOCALIZATION: Dict[str, str] = dict()
    _ENCRYPTION_KEY = None

    @staticmethod
    def _get_encryption_key():
        """Get or generate encryption key for cache files"""
        if FileManager._ENCRYPTION_KEY is None:
            key_file = os.path.join(FileManager.ASSETS_DIR, ".cache.key")
            if os.path.exists(key_file):
                with open(key_file, "rb") as f:
                    FileManager._ENCRYPTION_KEY = f.read()
            else:
                FileManager._ENCRYPTION_KEY = Fernet.generate_key()
                # Create assets dir if needed
                if not os.path.exists(FileManager.ASSETS_DIR):
                    os.makedirs(FileManager.ASSETS_DIR)
                # Save key with restricted permissions
                with open(key_file, "wb") as f:
                    os.chmod(key_file, stat.S_IRUSR | stat.S_IWUSR)  # 600 permissions
                    f.write(FileManager._ENCRYPTION_KEY)
        return FileManager._ENCRYPTION_KEY

    @staticmethod
    def load_localization(file: str):
        """
        Read localization file and store locale defined with environmental variable.

        :param file: Localization file path, related to current file (in sources root).
        """
        with open(join(dirname(__file__), file), encoding="utf-8") as config_file:
            data = load_json(config_file)
        FileManager._LOCALIZATION = data[EM.LOCALE]

    @staticmethod
    def t(key: str) -> str:
        """
        Translate string to current localization.

        :param key: Localization key.
        :returns: Translation string.
        """
        return FileManager._LOCALIZATION[key]

    @staticmethod
    def _validate_safe_path(base_dir: str, file_path: str) -> str:
        """
        Validate and normalize file path to prevent directory traversal.
        
        Args:
            base_dir: The base directory that should contain the file
            file_path: The requested file path
            
        Returns:
            Normalized absolute path if safe
            
        Raises:
            ValueError: If path validation fails
        """
        # Get absolute paths
        base_dir = os.path.abspath(base_dir)
        requested_path = os.path.abspath(os.path.join(base_dir, os.path.basename(file_path)))
        
        # Check if normalized path starts with base directory
        if not requested_path.startswith(base_dir):
            raise ValueError("Invalid file path - attempted directory traversal")
            
        # Check for symbolic links
        if os.path.islink(requested_path):
            raise ValueError("Symbolic links are not allowed")
            
        # Verify path exists and is within allowed directory
        common_prefix = os.path.commonpath([base_dir, requested_path])
        if common_prefix != base_dir:
            raise ValueError("Invalid file path - outside allowed directory")
            
        return requested_path

    @staticmethod
    def write_file(name: str, content: str, append: bool = False, assets: bool = False):
        """
        Save output file securely.

        Args:
            name: File name
            content: File content (utf-8 string)
            append: True for appending to file, false for rewriting
            assets: True for saving to 'assets' directory, false otherwise
            
        Raises:
            ValueError: If path validation fails
        """
        try:
            # Validate filename
            if not re.match(r'^[\w\-. ]+$', name):
                raise ValueError("Invalid filename format")
                
            # Determine base directory
            base_dir = os.path.abspath(FileManager.ASSETS_DIR if assets else os.curdir)
            
            # Create assets directory if needed
            if assets and not os.path.exists(base_dir):
                os.makedirs(base_dir, mode=0o755)
                
            # Get validated safe path
            safe_path = FileManager._validate_safe_path(base_dir, name)
            
            # Write file with secure permissions
            with open(safe_path, "a" if append else "w", encoding="utf-8") as f:
                # Set secure file permissions before writing
                os.chmod(safe_path, 0o644)  # rw-r--r--
                f.write(content)
                
        except Exception as e:
            raise ValueError(f"Failed to write file: {str(e)}")

    @staticmethod
    def cache_binary(name: str, content: Any = None, assets: bool = False) -> Optional[Any]:
        """Enhanced secure cache with better encryption
        
        Uses JSON serialization instead of pickle for security.
        Pickle is deliberately avoided due to remote code execution risks.
        """
        try:
            # Validate filename
            if not re.match(r'^[\w\-. ]+$', name):
                raise ValueError("Invalid cache filename")
                
            if assets:
                cache_dir = os.path.abspath(FileManager.ASSETS_DIR)
                if not os.path.exists(cache_dir):
                    os.makedirs(cache_dir, mode=0o700)  # Secure permissions
                filepath = os.path.join(cache_dir, name)
                
                # Prevent directory traversal
                if not os.path.abspath(filepath).startswith(cache_dir):
                    raise ValueError("Invalid cache path")
            else:
                filepath = os.path.abspath(name)

            fernet = Fernet(FileManager._get_encryption_key())
            
            if content is not None:
                # Serialize data securely
                json_data = json.dumps(content)
                encrypted_data = fernet.encrypt(json_data.encode())
                with open(filepath, 'wb') as f:
                    f.write(encrypted_data)
                return None
            
            try:
                with open(filepath, 'rb') as f:
                    encrypted_data = f.read()
                try:
                    decrypted_data = fernet.decrypt(encrypted_data)
                    return json.loads(decrypted_data)
                except InvalidToken:
                    return None
            except FileNotFoundError:
                return None
        except Exception as e:
            # Use DBM for logging
            error_msg = str(e)
            if "token" in error_msg.lower():
                error_msg = "[REDACTED TOKEN ERROR]"
            DBM.w(f"Cache error: {error_msg}")
            return None

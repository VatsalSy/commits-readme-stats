from copyreg import pickle
import os
from os.path import join, isfile, dirname, exists
from pickle import load as load_pickle, dump as dump_pickle
from json import load as load_json
from typing import Dict, Optional, Any
from os import makedirs
from cryptography.fernet import Fernet, InvalidToken
import stat
import io
import re
from functools import wraps
from time import sleep
import signal
from contextlib import contextmanager
import json

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
    def write_file(name: str, content: str, append: bool = False, assets: bool = False):
        """
        Save output file.

        :param name: File name.
        :param content: File content (utf-8 string).
        :param append: True for appending to file, false for rewriting.
        :param assets: True for saving to 'assets' directory, false otherwise.
        :raises ValueError: If path traversal is detected
        """
        # Get safe filename
        safe_name = os.path.basename(name)
        
        if assets:
            # Ensure assets directory exists
            if not os.path.exists(FileManager.ASSETS_DIR):
                os.makedirs(FileManager.ASSETS_DIR)
            safe_path = os.path.abspath(os.path.join(FileManager.ASSETS_DIR, safe_name))
            # Verify the path is within assets directory
            if not safe_path.startswith(os.path.abspath(FileManager.ASSETS_DIR)):
                raise ValueError("Invalid file path - attempted directory traversal")
        else:
            safe_path = os.path.abspath(safe_name)
            # Verify path is in current directory
            if not safe_path.startswith(os.path.abspath(os.curdir)):
                raise ValueError("Invalid file path - attempted directory traversal")

        with open(safe_path, "a" if append else "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def cache_binary(name: str, content: Any = None, assets: bool = False) -> Optional[Any]:
        """Enhanced secure cache with better encryption"""
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

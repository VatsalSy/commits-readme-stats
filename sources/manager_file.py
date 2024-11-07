import os
from os.path import join, isfile, dirname, exists
from pickle import load as load_pickle, dump as dump_pickle
from json import load as load_json
from typing import Dict, Optional, Any
from os import makedirs
from cryptography.fernet import Fernet
import stat
import io

from .manager_environment import EnvironmentManager as EM


def init_localization_manager():
    """
    Initialize localization manager.
    Load GUI translations JSON file.
    """
    FileManager.load_localization("translation.json")


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
        """Cache binary data to file with encryption."""
        if assets:
            if not exists(FileManager.ASSETS_DIR):
                makedirs(FileManager.ASSETS_DIR)
            name = join(FileManager.ASSETS_DIR, name)

        # Initialize encryption
        fernet = Fernet(FileManager._get_encryption_key())

        if content is None:
            if not isfile(name):
                return None
            try:
                with open(name, "rb") as file:
                    encrypted_data = file.read()
                    decrypted_data = fernet.decrypt(encrypted_data)
                    return load_pickle(io.BytesIO(decrypted_data))
            except Exception as e:
                DBM.w(f"Failed to load cache: {str(e)}")
                return None
        else:
            try:
                # Pickle and encrypt the data
                pickled_data = io.BytesIO()
                dump_pickle(content, pickled_data)
                encrypted_data = fernet.encrypt(pickled_data.getvalue())
                
                # Save with restricted permissions
                with open(name, "wb") as file:
                    os.chmod(name, stat.S_IRUSR | stat.S_IWUSR)  # 600 permissions
                    file.write(encrypted_data)
                return None
            except Exception as e:
                DBM.w(f"Failed to save cache: {str(e)}")
                return None

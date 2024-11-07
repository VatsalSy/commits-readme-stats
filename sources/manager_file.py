from os.path import join, isfile, dirname, exists
from pickle import load as load_pickle, dump as dump_pickle
from json import load as load_json
from typing import Dict, Optional, Any
from os import makedirs

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
        """
        name = join(FileManager.ASSETS_DIR, name) if assets else name
        with open(name, "a" if append else "w", encoding="utf-8") as file:
            file.write(content)

    @staticmethod
    def cache_binary(name: str, content: Any = None, assets: bool = False) -> Optional[Any]:
        """
        Cache binary data to file.
        If content is None, loads and returns data from file.
        Otherwise saves content to file.
        """
        if assets:
            # Create assets directory if it doesn't exist
            assets_dir = "assets"
            if not exists(assets_dir):
                makedirs(assets_dir)
            name = join(assets_dir, name)

        if content is None:
            if not isfile(name):
                return None
            with open(name, "rb") as file:
                return load_pickle(file)
        else:
            with open(name, "wb") as file:
                dump_pickle(content, file)
            return None

"""Copy settings feature implementation for Graylint.

This module provides the in-memory storage mechanism for settings files
specified via --copy-settings/-S CLI arguments.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CopySettingsStorage:
    """In-memory storage for settings file contents."""

    def __init__(self) -> None:
        """Initialize the storage."""
        self._storage: dict[str, str] = {}

    def load_files(self, root: Path, relative_paths: list[str]) -> None:
        """Load settings files into memory.

        - Missing files are logged as warnings and skipped
        - Files are read as UTF-8 text
        - Original paths are preserved as keys

        :param file_paths: List of file paths to load
        """
        self._storage.clear()

        for file_path in relative_paths:
            relative_path = Path(file_path)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                msg = (
                    "copy-settings path must be relative to the project root"
                    f" and not contain '..': {file_path}"
                )
                raise ValueError(msg)
            path = root / relative_path
            try:
                if not path.exists():
                    logger.warning("Settings file not found: %s", file_path)
                    continue

                if not path.is_file():
                    logger.warning("Path is not a file: %s", file_path)
                    continue

                content = path.read_text(encoding="utf-8")
                self._storage[file_path] = content
                logger.debug("Loaded settings file: %s", file_path)

            except OSError as e:
                logger.warning("Error reading settings file %s: %s", file_path, e)
            except UnicodeDecodeError as e:
                logger.warning(
                    "Cannot decode settings file %s as UTF-8: %s", file_path, e
                )

    def get_all_contents(self) -> dict[str, str]:
        """Get all file contents.

        :return: Dictionary mapping file paths to contents
        """
        return self._storage.copy()

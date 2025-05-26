"""Encapsulate path/device/stdout handling in a class."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TextIO


class OutputDestination:
    """Encapsulate path/device/stdout handling in a class."""

    def __init__(self, path_or_dash: Path) -> None:
        """Initialize the output destination class."""
        if path_or_dash == Path("-"):
            self._path: Path | None = None
            self._file: TextIO | None = sys.stdout
        else:
            self._path = path_or_dash
            self._file = None

    def open(self) -> TextIO:
        """Open the output destination for writing.

        :raises TypeError: If the output destination object is invalid.

        """
        if self._file == sys.stdout and self._path is None:
            return sys.stdout
        if isinstance(self._path, Path) and self._file is None:
            self._file = self._path.open("w")
            return self._file
        message = f"Invalid OutputDestination object {self!r}"
        raise TypeError(message)

    def close(self) -> None:
        """Close the output destination."""
        if self._file is not None and self._file != sys.stdout:
            self._file.close()

    @property
    def path(self) -> Path:
        """The path to the output destination."""
        if self._file == sys.stdout and self._path is None:
            message = "stdout has no path"
            raise ValueError(message)
        if isinstance(self._path, Path):
            return self._path
        message = f"Invalid OutputDestination object {self!r}"
        raise TypeError(message)

    def __repr__(self) -> str:
        """Return a string representation of the path or device."""
        path = "-" if self._file == sys.stdout else self._path
        return f"{self.__class__.__name__}({path!r})"

    def __eq__(self, other: object) -> bool:
        """Compare two output destinations."""
        if not isinstance(other, OutputDestination):
            return False
        return self._path == other._path

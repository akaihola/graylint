"""Data types for linter error messages and their locations in a file."""

import sys
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


@dataclass(eq=True, frozen=True, order=True)
class MessageLocation:
    """A file path, line number and column number for a linter message.

    Line and column numbers a 0-based, and zero is used for an unspecified column, and
    for the non-specified location.

    """

    path: Path
    line: int
    column: int = 0

    @override
    def __str__(self) -> str:
        """Convert file path, line and column into a linter line prefix string.

        :return: Either ``"path:line:column"`` or ``"path:line"`` (if column is zero)

        """
        if self.column:
            return f"{self.path}:{self.line}:{self.column}"
        return f"{self.path}:{self.line}"


DISCARDED_LINE = MessageLocation(Path(), 0, -1)
INVALID_LINE = MessageLocation(Path(), 0, -2)


@dataclass
class LinterMessage:
    """Information about a linter message."""

    linter: str
    description: str

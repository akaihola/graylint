"""Base class for linter parsers."""

from abc import ABC, abstractmethod
from pathlib import Path

from graylint.linter_parser.message import LinterMessage, MessageLocation


class LinterParser(ABC):  # pylint: disable=too-few-public-methods
    """Base class for linter parsers."""

    name = "base-linter-parser"

    @abstractmethod
    def parse(
        self, linter: str, linter_output: str, cwd: Path
    ) -> dict[MessageLocation, list[LinterMessage]]:
        """Parse the output of a linter.

        :param linter_output: The complete output of the linter
        :return: A mapping of linter message locations to linter messages

        """
        raise NotImplementedError


class ParserError(Exception):
    """Exception raised when a linter parser fails to parse a linter output."""

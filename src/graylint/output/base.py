"""Base class for output plugins."""

from __future__ import annotations

from os import devnull
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import sys
    from typing import Literal, TextIO

    if sys.version_info >= (3, 10):
        from typing import Self
    else:
        from typing_extensions import Self

    from graylint.linter_parser.message import LinterMessage, MessageLocation
    from graylint.output.destination import OutputDestination


# pylint: disable=consider-using-with
NULL_STREAM: TextIO = Path(devnull).open("w", encoding="utf-8")  # noqa: SIM115


class OutputPlugin:
    """Base class for output plugins."""

    def __init__(self, destination: OutputDestination, *, use_color: bool) -> None:
        """Initialize the output plugin."""
        self._destination: OutputDestination = destination
        self._use_color: bool = use_color
        self._stream: TextIO = NULL_STREAM

    def __enter__(self) -> Self:
        """Open the output stream to enter the context manager."""
        self._stream = self._destination.open()
        return self

    def __exit__(
        self, exc_type: object, exc_value: object, traceback: object
    ) -> Literal[False]:
        """Close the output stream to exit the context manager."""
        self._destination.close()
        self._stream = NULL_STREAM
        return False

    def output(self, location: MessageLocation, message: LinterMessage) -> None:
        """Output a message in the desired format."""
        raise NotImplementedError

    def group_delimiter(self) -> None:
        """Output a delimiter between groups of messages."""

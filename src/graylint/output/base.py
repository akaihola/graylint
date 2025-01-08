"""Base class for output plugins."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Self

if TYPE_CHECKING:
    from graylint.linting import LinterMessage, MessageLocation
    from graylint.output.destination import OutputDestination


class OutputPlugin:
    """Base class for output plugins."""

    def __init__(self, destination: OutputDestination, *, use_color: bool) -> None:
        """Initialize the output plugin."""
        self._destination = destination
        self._use_color = use_color

    def __enter__(self) -> Self:
        """Open the output stream to enter the context manager."""
        self._stream = self._destination.open()
        return self

    def __exit__(
        self, exc_type: object, exc_value: object, traceback: object
    ) -> Literal[False]:
        """Close the output stream to exit the context manager."""
        self._destination.close()
        return False

    def output(self, location: MessageLocation, message: LinterMessage) -> None:
        """Output a message in the desired format."""
        raise NotImplementedError

    def group_delimiter(self) -> None:
        """Output a delimiter between groups of messages."""

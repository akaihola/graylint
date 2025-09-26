"""Output plugin for GNU error format."""

from darkgraylib.highlighting import colorize
from graylint.linter_parser.message import LinterMessage, MessageLocation
from graylint.output.base import OutputPlugin


class GnuErrorFormatOutputPlugin(OutputPlugin):
    """Output plugin for GNU error format."""

    def output(self, location: MessageLocation, message: LinterMessage) -> None:
        """Output a message in the GNU error format."""
        loc = (
            f"{location.path}:{location.line}:{location.column}:"
            if location.column
            else f"{location.path}:{location.line}:"
        )
        print(
            colorize(loc, "lint_location", self._use_color), end=" ", file=self._stream
        )
        print(
            colorize(message.description, "lint_description", self._use_color),
            end=" ",
            file=self._stream,
        )
        print(f"[{message.linter}]", file=self._stream)

    def group_delimiter(self) -> None:
        """Output a delimiter between groups of messages."""
        print(file=self._stream)

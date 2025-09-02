"""GitHub output plugin for Graylint."""

from graylint.linter_parser.message import LinterMessage, MessageLocation
from graylint.output.base import OutputPlugin


class GitHubOutputPlugin(OutputPlugin):
    """Output plugin for GitHub message annotations."""

    def output(self, location: MessageLocation, message: LinterMessage) -> None:
        """Output a message in the GitHub message annotation format."""
        print("::error", end=" ", file=self._stream)
        print(f"file={location.path}", end=",", file=self._stream)
        print(f"line={location.line}", end=",", file=self._stream)
        if location.column:
            print(f"col={location.column}", end=",", file=self._stream)
        print(f"title={message.linter}::{message.description}", file=self._stream)

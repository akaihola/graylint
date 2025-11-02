"""Parser plugin for GNU error format."""

import logging
from collections import defaultdict
from pathlib import Path

from graylint.linter_parser.base import LinterParser
from graylint.linter_parser.message import INVALID_LINE, LinterMessage, MessageLocation

logger = logging.getLogger(__name__)


def _strict_nonneg_int(text: str) -> int:
    """Strict parsing of strings to non-negative integers.

    Allow no leading or trailing whitespace, nor plus or minus signs.

    :param text: The string to convert
    :raises ValueError: Raises if the string has any non-numeric characters
    :return: The parsed non-negative integer value

    """
    if text.strip("+-\t ") != text:
        msg = f"invalid literal for int() with base 10: {text}"
        raise ValueError(msg)
    return int(text)


class GnuErrorFormatParserPlugin(LinterParser):
    """GNU error format parser plugin."""

    name = "gnu"

    def parse(
        self, linter: str, linter_output: str, cwd: Path  # noqa: ARG002
    ) -> dict[MessageLocation, list[LinterMessage]]:
        """Parse the output of a linter which uses GNU error format.

        :param linter_output: The complete output of the linter
        :return: A mapping of linter message locations to linter messages

        """
        messages: dict[MessageLocation, list[LinterMessage]] = defaultdict(list)
        for line in linter_output.splitlines(keepends=True):
            location, message = self.parse_gnu_error_line(linter, line)
            if location != INVALID_LINE:
                messages[location].append(message)
        return messages

    def parse_gnu_error_line(
        self, linter: str, line: str
    ) -> tuple[MessageLocation, LinterMessage]:
        """Parse one line of linter output.

        Only parses lines with
        - a relative or absolute file path (without leading-trailing whitespace),
        - a non-negative line number (without leading/trailing whitespace),
        - optionally a column number (without leading/trailing whitespace), and
        - a description.

        Examples of successfully parsed lines::

            path/to/file.py:42: Description
            /absolute/path/to/file.py:42:5: Description

        These would be parsed into::

            (
                MessageLocation(Path("path/to/file.py"), 42, 0),
                LinterMessage("linter", "Description"),
            )
            (
                MessageLocation(Path("/absolute/path/to/file.py"), 42, 5),
                LinterMessage("linter", "Description"),
            )

        For all other lines, an ``INVALID_LINE`` dummy entry is returned:
        an empty path, zero as the line number, -2 as the column,
        and an empty description.

        Such lines should be simply ignored, since many linters display supplementary
        information insterspersed with the actual linting notifications.

        Linter-specific plugins should enhance the parsing logic to return a
        ``DISCARDED_LINE`` dummy entry for any additional valid recognized output.
        Those entries will be counted towards the score of the plugin, and the highest
        scoring plugin will be used as the actual parser.

        :param linter: The name of the linter
        :param line: The linter output line to parse. May have a trailing newline.
        :return: A 2-tuple of objects with
                 - the file path, line and column numbers of the linter message, and
                 - the linter name and message description.

        """

        def _check_filename_whitespace(path_str: str) -> None:
            if path_str.strip() != path_str:
                msg = f"Filename {path_str!r} has leading/trailing whitespace"
                raise ValueError(msg)

        def _check_token_count(location: str, rest: list[str]) -> None:
            if len(rest) > 1:
                msg = f"Too many colon-separated tokens in {location!r}"
                raise ValueError(msg)

        try:
            location, description = line.rstrip().split(": ", 1)
            if location[1:3] == ":\\":
                # Absolute Windows paths need special handling. Separate out the ``C:``
                # (or similar), then split by colons, and finally re-insert the ``C:``.
                path_in_drive, linenum_str, *rest = location[2:].split(":")
                path_str = f"{location[:2]}{path_in_drive}"
            else:
                path_str, linenum_str, *rest = location.split(":")
            _check_filename_whitespace(path_str)
            linenum = _strict_nonneg_int(linenum_str)
            _check_token_count(location, rest)
            # Make sure the column looks like an int in "<path>:<linenum>:<column>":
            column = _strict_nonneg_int(rest[0]) if len(rest) == 1 else 0
        except ValueError as exc:
            # Encountered a non-parsable line which doesn't express a linting error.
            # For example, on Mypy:
            #   >Found XX errors in YY files (checked ZZ source files)
            #   >Success: no issues found in 1 source file
            logger.debug("Unparsable linter output: %s", line[:-1])
            logger.debug("Reason: %s", exc)
            return (INVALID_LINE, LinterMessage(linter, ""))
        path = Path(path_str)
        return (
            MessageLocation(path, linenum, column),
            LinterMessage(linter, description),
        )

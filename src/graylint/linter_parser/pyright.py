import logging
import re
from collections import defaultdict
from pathlib import Path

from graylint.linter_parser.base import LinterParser
from graylint.linter_parser.gnu import _strict_nonneg_int
from graylint.linter_parser.message import (
    DISCARDED_LINE,
    INVALID_LINE,
    LinterMessage,
    MessageLocation,
)

logger = logging.getLogger(__name__)


MESSAGE_LINE_RE = re.compile(
    r"""
    \ \             # (two-space indent)
    (.*?) :         # /home/me/path/file.py:
    (?:             # (maybe:)
        (\d+) :     #   21: (row)
        (\d+)       #   42  (column)
        \  -        #   <space> -
    )?
    \  (\w+) : \    # <space> error: <space>  OR  warning: <space>
    (.*) $          # (error message)
    """,
    re.VERBOSE,
)


class PyrightParserPlugin(LinterParser):
    def _parse_pyright_line(
        self, linter: str, line: str, cwd: Path
    ) -> tuple[MessageLocation, LinterMessage]:
        """Parse one line of Pyright or Basedpyright output

        Only parses lines with
        - a relative or absolute file path (without leading-trailing whitespace),
        - a non-negative line number (without leading/trailing whitespace),
        - a column number (without leading/trailing whitespace),
        - a message level (e.g. "error"), and
        - a description.

        Examples of a successfully parsed line::

            /absolute/path/to/file.py:42:5 - error: Description

        Given ``cwd=Path("/absolute")``, this would be parsed into::

            (Path("path/to/file.py"), 42, "path/to/file.py:42:5:", "Description")

        For all other lines, a dummy entry is returned: an empty path, zero as the line
        number, an empty location string and an empty description. Such lines should be
        simply ignored, since many linters display supplementary information
        insterspersed with the actual linting notifications.

        :param linter: The name of the linter
        :param line: The linter output line to parse. May have a trailing newline.
        :param cwd: The directory in which the linter was run, and relative to which
                    paths are returned
        :return: A 2-tuple of
                - the file path, line and column numbers of the linter message, and
                - the linter name and message description.

        """
        match = MESSAGE_LINE_RE.match(line)
        if not match:
            return (INVALID_LINE, LinterMessage(linter, ""))
        path = Path(match.group(1))
        linenum = 0 if match.group(2) is None else _strict_nonneg_int(match.group(2))
        column = 0 if match.group(3) is None else _strict_nonneg_int(match.group(3))
        severity = match.group(4)
        description = match.group(5)
        return (
            MessageLocation(path, linenum, column),
            LinterMessage(linter, f"{severity}: {description}"),
        )

    def parse(
        self, linter: str, linter_output: str, cwd: Path
    ) -> dict[MessageLocation, list[LinterMessage]]:
        """Parse the output of Pyright or Basedpyright

        :param linter_output: The complete output of the linter
        :return: A mapping of linter message locations to linter messages

        """
        messages: dict[MessageLocation, list[LinterMessage]] = defaultdict(list)
        location = INVALID_LINE
        path = Path()
        for line in linter_output.splitlines(keepends=True):
            if not line.startswith("  "):
                path = Path(line[:-1])
                if path.exists():
                    messages[DISCARDED_LINE].append(LinterMessage(linter, str(path)))
                continue
            if line.startswith(("  \u00a0\u00a0", "    ")):
                # continuation of a message
                # (First variant ends with two non-breaking spaces)
                messages[location].append(LinterMessage(linter, line[4:-1]))
                continue
            location, message = self._parse_pyright_line(linter, line, cwd)
            if location.path != path:
                logger.warning(
                    "Inconsistent path in Pyright output line: %s (expected %s)",
                    location.path,
                    path,
                )
            messages[location].append(message)
        return messages

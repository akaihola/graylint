"""Parser plugin for GNU error format."""

import logging
import os
import re
from collections import defaultdict
from collections.abc import Generator, Iterable, Iterator
from pathlib import Path
from typing import Match, Pattern

from graylint.linter_parser.base import LinterParser
from graylint.linter_parser.gnu import GnuErrorFormatParserPlugin
from graylint.linter_parser.message import (
    DISCARDED_LINE,
    INVALID_LINE,
    LinterMessage,
    MessageLocation,
)

logger = logging.getLogger(__name__)


R0801_RE = re.compile(r": R0801: Similar lines in (\d+) files$")
DUPLICATE_RE: Pattern[str] = re.compile(
    r"""                 # example:
    ==                   # ==
    (
      [^\d\W]\w*         # src
      (?:\.[^\d\W]\w*)*  # .graylint.linter_parser.pylint
    )
    : \[                 # :[
      (\d+) : (\d+)      #   21:29
    \]                   # ]
    """,
    re.VERBOSE,
)


class PylintParserPlugin(GnuErrorFormatParserPlugin):
    name = "pylint"

    def parse(
        self, linter: str, linter_output: str, cwd: Path
    ) -> dict[MessageLocation, list[LinterMessage]]:
        """Parse the output of a linter which uses GNU error format

        :param linter_output: The complete output of the linter
        :return: A mapping of linter message locations to linter messages

        """
        messages: dict[MessageLocation, list[LinterMessage]] = defaultdict(list)
        lines = iter(linter_output.splitlines(keepends=True))
        for location, message in self.parse_lines(linter, lines, cwd):
            if location is not INVALID_LINE:
                messages[location].append(message)
        return messages

    def parse_lines(
        self, linter: str, lines: Iterator[str], cwd: Path
    ) -> Generator[tuple[MessageLocation, LinterMessage]]:
        try:
            while True:
                line = next(lines)
                if not line.strip():
                    continue
                if line.startswith(
                    (
                        "************* Module ",
                        "Command line or configuration file:",
                        "-------------------------------------------------------------",
                        "Your code has been rated at ",
                    )
                ):
                    yield (DISCARDED_LINE, LinterMessage(linter, ""))
                    continue
                match = R0801_RE.search(line)
                if match:
                    # It's a "Similar lines in N files" message.
                    # Pylint outputs a bogus file path, line and column here.
                    # The actual files and similar lines are output below this.
                    yield (
                        DISCARDED_LINE,
                        LinterMessage(linter, match.group()[2:]),
                    )
                    yield from self.parse_R0801(linter, lines, cwd, match)
                    continue
                yield self.parse_gnu_error_line(linter, line)
        except StopIteration:
            pass

    def parse_R0801(
        self, linter: str, lines: Iterator[str], cwd: Path, match: Match[str]
    ) -> Iterator[tuple[MessageLocation, LinterMessage]]:
        num_duplicates = int(match.group(1))
        num_lines = 0
        for i in range(num_duplicates):
            line = next(lines)
            duplicate_match = DUPLICATE_RE.match(line)
            if not duplicate_match:
                yield self.parse_gnu_error_line(linter, line)
                return
            path = f"{duplicate_match.group(1).replace('.', os.sep)}.py"
            start_line = int(duplicate_match.group(2))
            yield (
                MessageLocation(Path(path), start_line + 1, 0),
                LinterMessage(linter, match.group()[2:]),
            )
            end_line = int(duplicate_match.group(3))
            num_lines_here = end_line - start_line
            if num_lines == 0:
                num_lines = num_lines_here
            elif num_lines_here != num_lines:
                logger.warning("Duplicated code length mismatch in: %s", line)
                if num_lines_here < num_lines:
                    # for robustness, go with the smaller number of code lines
                    num_lines = num_lines_here
        for i in range(num_lines):
            next(lines)

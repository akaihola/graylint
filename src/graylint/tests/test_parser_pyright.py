from pathlib import Path
from textwrap import dedent

import pytest

from graylint.linter_parser.message import (
    DISCARDED_LINE,
    INVALID_LINE,
    LinterMessage,
    MessageLocation,
)
from graylint.linter_parser.pyright import PyrightParserPlugin


@pytest.mark.kwparametrize(
    dict(
        line="foobar",
        expect=(INVALID_LINE, LinterMessage("basedpyright", "")),
    ),
    dict(
        line="  /path/file.py:21:42 - error: Nonsense code (reportNonsense)\n",
        expect=(
            MessageLocation(Path("/path/file.py"), 21, 42),
            LinterMessage(
                "basedpyright",
                "error: Nonsense code (reportNonsense)",
            ),
        ),
    ),
)
def test_parse_pyright_line(line, expect):
    result = PyrightParserPlugin()._parse_pyright_line("basedpyright", line, Path("."))
    assert result == expect


@pytest.mark.kwparametrize(
    dict(output="", expect={}),
    dict(
        output=dedent(
            """
            /path/file.py
              /path/file.py:21:42 - error: Nonsense code
                Additional info (reportNonsense)
            /path/first.py
              /path/first.py: error: Cycle detected in import chain
                /path/first.py
                /path/second (reportImportCycles)
            """
        ),
        expect={
            DISCARDED_LINE: [LinterMessage("basedpyright", ".")],
            MessageLocation(Path("/path/file.py"), 21, 42): [
                LinterMessage("basedpyright", "error: Nonsense code"),
                LinterMessage("basedpyright", "Additional info (reportNonsense)"),
            ],
            MessageLocation(Path("/path/first.py"), 0, 0): [
                LinterMessage("basedpyright", "error: Cycle detected in import chain"),
                LinterMessage("basedpyright", "/path/first.py"),
                LinterMessage("basedpyright", "/path/second (reportImportCycles)"),
            ],
        },
    ),
)
def test_parse(output, expect):
    result = PyrightParserPlugin().parse("basedpyright", output, Path("."))
    assert result == expect

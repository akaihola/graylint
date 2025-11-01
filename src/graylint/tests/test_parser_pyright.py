"""Tests for the Pyright parser plugin."""

from pathlib import Path
from textwrap import dedent

import pytest

from graylint.linter_parser.message import INVALID_LINE, LinterMessage, MessageLocation
from graylint.linter_parser.pyright import PyrightParserPlugin


@pytest.mark.kwparametrize(
    dict(
        line="foobar",
        expect=(INVALID_LINE, LinterMessage("basedpyright", "")),
    ),
    dict(
        line="  {root}/path/file.py:21:42 - error: Nonsense code (reportNonsense)\n",
        expect=(
            MessageLocation(Path("./path/file.py"), 21, 42),
            LinterMessage(
                "basedpyright",
                "error: Nonsense code (reportNonsense)",
            ),
        ),
    ),
)
def test_parse_pyright_line(tmp_path, line, expect):
    result = PyrightParserPlugin()._parse_pyright_line(
        "basedpyright", line.format(root=tmp_path), tmp_path
    )
    assert result == expect


@pytest.mark.kwparametrize(
    dict(output="", expect={}),
    dict(
        output=dedent(
            """
            {root}/path/file.py
              {root}/path/file.py:21:42 - error: Nonsense code
                Additional info (reportNonsense)
            {root}/path/first.py
              {root}/path/first.py: error: Cycle detected in import chain
                {root}/path/first.py
                {root}/path/second (reportImportCycles)
            """
        ),
        expect={
            MessageLocation(Path("./path/file.py"), 21, 42): [
                LinterMessage(
                    "basedpyright",
                    "error: Nonsense code\nAdditional info (reportNonsense)",
                ),
            ],
            MessageLocation(Path("./path/first.py"), 0, 0): [
                LinterMessage(
                    "basedpyright",
                    "error: Cycle detected in import chain\n"
                    "{root}/path/first.py\n"
                    "{root}/path/second (reportImportCycles)",
                ),
            ],
        },
    ),
)
def test_parse(tmp_path, output, expect):
    result = PyrightParserPlugin().parse(
        "basedpyright", output.format(root=tmp_path), tmp_path
    )
    for linter_messages in expect.values():
        for linter_message in linter_messages:
            linter_message.description = linter_message.description.format(
                root=tmp_path
            )
    assert result == expect

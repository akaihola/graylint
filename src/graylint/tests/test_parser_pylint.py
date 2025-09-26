"""Test the `PylintParserPlugin` class."""

from pathlib import Path
from textwrap import dedent

import pytest

from graylint.linter_parser.message import (
    DISCARDED_LINE,
    INVALID_LINE,
    LinterMessage,
    MessageLocation,
)
from graylint.linter_parser.pylint import DUPLICATE_RE, R0801_RE, PylintParserPlugin


@pytest.mark.kwparametrize(
    dict(
        output=["************* Module src.graylint.linter_parser.gnu"],
        expect=[
            (DISCARDED_LINE, LinterMessage("pylint", "")),
        ],
    ),
    dict(
        output=["my/source.py:30:0: C0301: Line too long (104/100) (line-too-long)"],
        expect=[
            (
                MessageLocation(Path("my/source.py"), 30, 0),
                LinterMessage(
                    "pylint", "C0301: Line too long (104/100) (line-too-long)"
                ),
            ),
        ],
    ),
    dict(
        output=[
            "action/tests/test_action_main.py:1:0: R0801: Similar lines in 2 files",
            "==linter_parser.pyright:[45:47]",
            "==linter_parser.pyright_json:[45:47]",
            "if not line.startswith(" "):",
            "    return (NO_MESSAGE_LOCATION, LinterMessage(linter, " "))",
            "",
            " (duplicate-code)",
        ],
        expect=[
            (
                DISCARDED_LINE,
                LinterMessage("pylint", "R0801: Similar lines in 2 files"),
            ),
            (
                MessageLocation(Path("linter_parser/pyright.py"), 46, 0),
                LinterMessage("pylint", "R0801: Similar lines in 2 files"),
            ),
            (
                MessageLocation(Path("linter_parser/pyright_json.py"), 46, 0),
                LinterMessage("pylint", "R0801: Similar lines in 2 files"),
            ),
            (INVALID_LINE, LinterMessage("pylint", "")),
        ],
    ),
)
def test_parse(
    output: str,
    expect: list[tuple[MessageLocation, LinterMessage]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    lines = iter(f"{line}\n" for line in output)
    result = list(PylintParserPlugin().parse_lines("pylint", lines, Path(".")))

    assert result == expect


@pytest.mark.kwparametrize(
    dict(
        line="==src.graylint.linter_parser.pyright:[45:81]",
        expect_module_path="src.graylint.linter_parser.pyright",
        expect_start=45,
        expect_end=81,
    ),
    dict(
        line="==src.graylint.linter_parser.pyright_json:[45:81]",
        expect_module_path="src.graylint.linter_parser.pyright_json",
        expect_start=45,
        expect_end=81,
    ),
)
def test_duplicate_re(
    line: str, expect_module_path: str, expect_start: int, expect_end: int
) -> None:
    match = DUPLICATE_RE.search(line)
    assert match is not None
    assert match.group(1) == expect_module_path
    assert int(match.group(2)) == expect_start
    assert int(match.group(3)) == expect_end

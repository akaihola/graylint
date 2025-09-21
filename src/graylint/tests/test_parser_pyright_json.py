import json
from pathlib import Path

import pytest

from graylint.linter_parser.message import (
    DISCARDED_LINE,
    LinterMessage,
    MessageLocation,
)
from graylint.linter_parser.pyright_json import PyrightJsonParserPlugin


def test_parse(output: str, expect: dict[MessageLocation, list[LinterMessage]]) -> None:
    output = json.dumps(
        {
            "generalDiagnostics": [
                {
                    "file": "subdir/first.py",
                    "severity": "error",
                    "message": "Everything's wrong.",
                    "range": {"start": {"line": 29, "character": 0}},
                    "rule": "reportDisaster",
                },
                {
                    "file": "subdir/second.py",
                    "severity": "warning",
                    "message": "Not advisable.",
                    "range": {"start": {"line": 14, "character": 4}},
                    "rule": "reportRisks",
                },
            ],
        }
    )
    expect = {
        DISCARDED_LINE: [LinterMessage("pyright", "generalDiagnostics")],
        MessageLocation(Path("subdir/first.py"), 29, 0): [
            LinterMessage(
                linter="pyright",
                description="error: Everything's wrong. (reportDisaster)",
            ),
        ],
        MessageLocation(Path("subdir/second.py"), 14, 4): [
            LinterMessage(
                linter="pyright",
                description="warning: Not advisable. (reportRisks)",
            ),
        ],
    }
    result = PyrightJsonParserPlugin().parse("pyright", output, Path("/absolute"))
    assert result == expect

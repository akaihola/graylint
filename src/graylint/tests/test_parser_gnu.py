"""Test the GNU error format parser plugin."""

import os
from pathlib import Path

import pytest

from darkgraylib.testtools.git_repo_plugin import GitRepoFixture
from graylint.linter_parser.gnu import GnuErrorFormatParserPlugin
from graylint.linter_parser.message import INVALID_LINE, LinterMessage, MessageLocation
from graylint.tests.testhelpers import SKIP_ON_UNIX, SKIP_ON_WINDOWS


@pytest.fixture
def gnu_parser() -> GnuErrorFormatParserPlugin:
    """Fixture for the GNU error format parser plugin."""
    return GnuErrorFormatParserPlugin()


@pytest.fixture(scope="module")
def parse_linter_line_repo(request, tmp_path_factory):
    """Git repository fixture for `test_parse_linter_line`."""
    with GitRepoFixture.context(request, tmp_path_factory) as repo:
        yield repo


def test_empty(gnu_parser: GnuErrorFormatParserPlugin) -> None:
    """Test parsing an empty string."""
    messages = gnu_parser.parse("linter", "", Path("/cwd"))
    assert messages == {}


@pytest.mark.kwparametrize(
    dict(
        line="module.py:42: Just a line number\n",
        expect=("module.py", 42, 0, "Just a line number"),
    ),
    dict(
        line="module.py:42:5: With column  \n",
        expect=("module.py", 42, 5, "With column"),
    ),
    dict(
        line="{git_root_absolute}{sep}mod.py:42: Full path\n",
        expect=("{git_root_absolute}{sep}mod.py", 42, 0, "Full path"),
    ),
    dict(
        line="{git_root_absolute}{sep}mod.py:42:5: Full path with column\n",
        expect=("{git_root_absolute}{sep}mod.py", 42, 5, "Full path with column"),
    ),
    dict(
        line="mod.py:42: 123 digits start the description\n",
        expect=("mod.py", 42, 0, "123 digits start the description"),
    ),
    dict(
        line="mod.py:42:    indented description\n",
        expect=("mod.py", 42, 0, "   indented description"),
    ),
    dict(
        line="mod.py:42:5:    indented description\n",
        expect=("mod.py", 42, 5, "   indented description"),
    ),
    dict(
        line="nonpython.txt:5: Non-Python file\n",
        expect=("nonpython.txt", 5, 0, "Non-Python file"),
    ),
    dict(line="mod.py: No line number\n", expect=INVALID_LINE),
    dict(line="mod.py:foo:5: Invalid line number\n", expect=INVALID_LINE),
    dict(line="mod.py:42:bar: Invalid column\n", expect=INVALID_LINE),
    dict(
        line="/outside/mod.py:5: Outside the repo\n",
        expect=("/outside/mod.py", 5, 0, "Outside the repo"),
        marks=SKIP_ON_WINDOWS,
    ),
    dict(
        line="C:\\outside\\mod.py:5: Outside the repo\n",
        expect=("C:\\outside\\mod.py", 5, 0, "Outside the repo"),
        marks=SKIP_ON_UNIX,
    ),
    dict(line="invalid linter output\n", expect=INVALID_LINE),
    dict(line=" leading:42: whitespace\n", expect=INVALID_LINE),
    dict(line=" leading:42:5 whitespace and column\n", expect=INVALID_LINE),
    dict(line="trailing :42: filepath whitespace\n", expect=INVALID_LINE),
    dict(line="leading: 42: linenum whitespace\n", expect=INVALID_LINE),
    dict(line="trailing:42 : linenum whitespace\n", expect=INVALID_LINE),
    dict(line="plus:+42: before linenum\n", expect=INVALID_LINE),
    dict(line="minus:-42: before linenum\n", expect=INVALID_LINE),
    dict(line="plus:42:+5 before column\n", expect=INVALID_LINE),
    dict(line="minus:42:-5 before column\n", expect=INVALID_LINE),
)
def test_parse_linter_line(
    parse_linter_line_repo, gnu_parser, monkeypatch, line, expect
):
    """Linter output is parsed correctly."""
    root = parse_linter_line_repo.root
    monkeypatch.chdir(root)
    root_abs = root.absolute()
    line_expanded = line.format(git_root_absolute=root_abs, sep=os.sep)

    result = gnu_parser.parse_gnu_error_line("linter", line_expanded)

    if expect is INVALID_LINE:
        expect_location = INVALID_LINE
        expect_message = LinterMessage("linter", "")
    else:
        expect_location = MessageLocation(
            Path(expect[0].format(git_root_absolute=root_abs, sep=os.sep)), *expect[1:3]
        )
        expect_message = LinterMessage("linter", expect[3])
    assert result == (expect_location, expect_message)

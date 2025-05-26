"""Tests for `graylint.output.github.GitHubOutputPlugin`."""

import os
from pathlib import Path

import pytest

from graylint.linting import LinterMessage, MessageLocation
from graylint.output.destination import OutputDestination
from graylint.output.github import GitHubOutputPlugin


@pytest.mark.kwparametrize(
    dict(
        path=Path("test.py"),
        line=10,
        column=0,
        linter="flake8",
        description="E501 line too long",
        expected="::error file=test.py,line=10,title=flake8::E501 line too long\n",
    ),
    dict(
        path=Path("src/module.py"),
        line=42,
        column=5,
        linter="pylint",
        description="missing-docstring",
        expected=(
            f"::error file=src{os.sep}module.py,"
            "line=42,col=5,title=pylint::missing-docstring\n"
        ),
    ),
    dict(
        path=Path("path with spaces.py"),
        line=7,
        column=3,
        linter="mypy",
        description='Type error: "str" has no attribute "nonexistent"',
        expected=(
            "::error file=path with spaces.py,line=7,col=3,"
            'title=mypy::Type error: "str" has no attribute "nonexistent"\n'
        ),
    ),
)
def test_github_output_plugin(
    capsys, path, line, column, linter, description, expected
):
    """GitHubOutputPlugin.output() formats messages in GitHub Actions format."""
    # Create a destination using "-" which will use sys.stdout
    destination = OutputDestination(Path("-"))
    plugin = GitHubOutputPlugin(destination, use_color=False)

    # Use the context manager to properly initialize the plugin
    with plugin:
        location = MessageLocation(path=path, line=line, column=column)
        message = LinterMessage(linter=linter, description=description)
        plugin.output(location, message)

    # Check the output
    captured = capsys.readouterr()
    assert captured.out == expected

"""Tests for the `graylint.__main__` module."""

from pathlib import Path
from unittest.mock import Mock, patch, DEFAULT

import pytest

from darkgraylib.utils import TextDocument
from graylint.__main__ import main


@pytest.mark.kwparametrize(
    dict(check=False, changes=False, lintfail=False),
    dict(check=False, changes=False, lintfail=True, expect_retval=1),
    dict(check=False, changes=True, lintfail=False),
    dict(check=False, changes=True, lintfail=True, expect_retval=1),
    dict(check=True, changes=False, lintfail=False),
    dict(check=True, changes=True, lintfail=True, expect_retval=1),
    expect_retval=0,
)
def test_main_retval(git_repo, check, changes, lintfail, expect_retval):
    """main() return value is correct based on --check, reformatting and linters"""
    git_repo.add({"a.py": ""}, commit="Initial commit")
    format_edited_parts = Mock()
    format_edited_parts.return_value = (
        [
            (
                Path("/dummy.py"),
                TextDocument.from_lines(["old"]),
                TextDocument.from_lines(["new"]),
            )
        ]
        if changes
        else []
    )
    run_linters = Mock(return_value=lintfail)
    check_arg_maybe = ["--check"] if check else []
    with patch.multiple(
        "darker.__main__",
        format_edited_parts=format_edited_parts,
        modify_file=DEFAULT,
        run_linters=run_linters,
    ):

        retval = main(check_arg_maybe + ["a.py"])

    assert retval == expect_retval

"""Tests for the `graylint.__main__` module."""

import os
from contextlib import nullcontext
from unittest.mock import Mock, patch

import pytest

from graylint.__main__ import main, main_with_error_handling


@pytest.mark.kwparametrize(
    dict(numfails=0, expect_retval=0),
    dict(numfails=1, expect_retval=1),
    dict(numfails=2, expect_retval=1),
)
def test_main_retval(numfails, expect_retval):
    """main() return value is correct based on linter results."""
    with patch("graylint.__main__.run_linters", Mock(return_value=numfails)):
        # end of test setup

        retval = main(["a.py"])

    assert retval == expect_retval


@pytest.mark.kwparametrize(
    dict(arguments=["{repo_root}"], expect_retval=0),
    dict(
        arguments=["--lint", "echo subdir/a.py:1: message", "{repo_root}"],
        expect_retval=1,
        expect_output=f"\nsubdir{os.sep}a.py:1: message . [echo]\n",
    ),
    dict(arguments=["a.py"], expect_retval=0),
    dict(arguments=["--config", "my.cfg", "a.py"], expect_retval=0),
    dict(
        arguments=["--invalid-option"],
        expect_retval=3,
        expect_exit=pytest.raises(SystemExit, match="3"),
    ),
    expect_output="",
    expect_exit=nullcontext(),
)
def test_main(
    git_repo,
    capsys,
    arguments,
    expect_retval,
    expect_output,
    expect_exit,
):
    """Main function return value is 1 if there are linter errors."""
    paths = git_repo.add({"subdir/a.py": "\n", "my.cfg": ""}, commit="Initial commit")
    paths["subdir/a.py"].write_text("Foo\n")
    rendered_arguments = [
        argument.format(repo_root=str(git_repo.root)) for argument in arguments
    ]
    with expect_exit:

        retval = main_with_error_handling(rendered_arguments)

        assert retval == expect_retval
    assert capsys.readouterr().out == expect_output

"""Tests for the `graylint.__main__` module."""

from unittest.mock import Mock, patch

import pytest

from graylint.__main__ import main


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
    dict(arguments=[], expect_retval=0),
    dict(arguments=["--lint", "echo subdir/a.py:1: message"], expect_retval=1),
)
def test_main(git_repo, arguments, expect_retval):
    """Main function return value is 1 if there are linter errors."""
    paths = git_repo.add({"subdir/a.py": "\n"}, commit="Initial commit")
    paths["subdir/a.py"].write_text("Foo\n")

    retval = main([*arguments, str(git_repo.root)])

    assert retval == expect_retval

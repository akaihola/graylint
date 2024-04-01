"""Tests for the `graylint.__main__` module."""

from pathlib import Path
from textwrap import dedent
from unittest.mock import Mock, patch

import darker
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


A_PY = ["import sys", "import os", "print( '{}'.format('42'))", ""]
A_PY_ISORT = ["import os", "import sys", "", "print( '{}'.format('42'))", ""]
A_PY_BLACK = ["import sys", "import os", "", 'print("{}".format("42"))', ""]
A_PY_BLACK_UNNORMALIZE = ("import sys", "import os", "", "print('{}'.format('42'))", "")
A_PY_BLACK_ISORT = ["import os", "import sys", "", 'print("{}".format("42"))', ""]
A_PY_BLACK_FLYNT = ["import sys", "import os", "", 'print("42")', ""]
A_PY_BLACK_ISORT_FLYNT = ["import os", "import sys", "", 'print("42")', ""]

A_PY_DIFF_BLACK = [
    "--- a.py",
    "+++ a.py",
    "@@ -1,3 +1,4 @@",
    " import sys",
    " import os",
    "-print( '{}'.format('42'))",
    "+",
    '+print("{}".format("42"))',
]

A_PY_DIFF_BLACK_NO_STR_NORMALIZE = [
    "--- a.py",
    "+++ a.py",
    "@@ -1,3 +1,4 @@",
    " import sys",
    " import os",
    "-print( '{}'.format('42'))",
    "+",
    "+print('{}'.format('42'))",
]

A_PY_DIFF_BLACK_ISORT = [
    "--- a.py",
    "+++ a.py",
    "@@ -1,3 +1,4 @@",
    "+import os",
    " import sys",
    "-import os",
    "-print( '{}'.format('42'))",
    "+",
    '+print("{}".format("42"))',
]

A_PY_DIFF_BLACK_FLYNT = [
    "--- a.py",
    "+++ a.py",
    "@@ -1,3 +1,4 @@",
    " import sys",
    " import os",
    "-print( '{}'.format('42'))",
    "+",
    '+print("42")',
]


@pytest.mark.kwparametrize(
    dict(arguments=["--diff"], expect_stdout=A_PY_DIFF_BLACK),
    dict(arguments=["--isort"], expect_a_py=A_PY_BLACK_ISORT),
    dict(arguments=["--flynt"], expect_a_py=A_PY_BLACK_FLYNT),
    dict(
        arguments=["--skip-string-normalization", "--diff"],
        expect_stdout=A_PY_DIFF_BLACK_NO_STR_NORMALIZE,
    ),
    dict(arguments=[], expect_a_py=A_PY_BLACK, expect_retval=0),
    dict(arguments=["--isort", "--diff"], expect_stdout=A_PY_DIFF_BLACK_ISORT),
    dict(arguments=["--flynt", "--diff"], expect_stdout=A_PY_DIFF_BLACK_FLYNT),
    dict(arguments=["--check"], expect_a_py=A_PY, expect_retval=1),
    dict(
        arguments=["--check", "--diff"],
        expect_stdout=A_PY_DIFF_BLACK,
        expect_retval=1,
    ),
    dict(arguments=["--check", "--isort"], expect_retval=1),
    dict(arguments=["--check", "--flynt"], expect_retval=1),
    dict(
        arguments=["--check", "--diff", "--isort"],
        expect_stdout=A_PY_DIFF_BLACK_ISORT,
        expect_retval=1,
    ),
    dict(
        arguments=["--check", "--diff", "--flynt"],
        expect_stdout=A_PY_DIFF_BLACK_FLYNT,
        expect_retval=1,
    ),
    dict(
        arguments=["--check", "--lint", "echo subdir/a.py:1: message"],
        # Windows compatible path assertion using `pathlib.Path()`
        expect_stdout=["", f"{Path('subdir/a.py')}:1: message {Path('subdir')} [echo]"],
        expect_retval=1,
    ),
    dict(
        arguments=["--diff", "--lint", "echo subdir/a.py:1: message"],
        # Windows compatible path assertion using `pathlib.Path()`
        expect_stdout=A_PY_DIFF_BLACK
        + ["", f"{Path('subdir/a.py')}:1: message {Path('subdir')} [echo]"],
        expect_retval=1,
    ),
    dict(
        arguments=[],
        pyproject_toml="""
           [tool.black]
           exclude = 'a.py'
           """,
        expect_a_py=A_PY,
    ),
    dict(
        arguments=["--diff"],
        pyproject_toml="""
           [tool.black]
           exclude = 'a.py'
           """,
        expect_stdout=[],
    ),
    dict(
        arguments=[],
        pyproject_toml="""
           [tool.black]
           extend_exclude = 'a.py'
           """,
        expect_a_py=A_PY,
    ),
    dict(
        arguments=["--diff"],
        pyproject_toml="""
           [tool.black]
           extend_exclude = 'a.py'
           """,
        expect_stdout=[],
    ),
    dict(
        arguments=[],
        pyproject_toml="""
           [tool.black]
           force_exclude = 'a.py'
           """,
        expect_a_py=A_PY,
    ),
    dict(
        arguments=["--diff"],
        pyproject_toml="""
           [tool.black]
           force_exclude = 'a.py'
           """,
        expect_stdout=[],
    ),
    dict(
        arguments=["--diff"],
        expect_stdout=A_PY_DIFF_BLACK,
        root_as_cwd=False,
    ),
    # for all test cases, by default there's no output, `a.py` stays unmodified, and the
    # return value is a zero:
    pyproject_toml="",
    expect_stdout=[],
    expect_a_py=A_PY,
    expect_retval=0,
    root_as_cwd=True,
)
@pytest.mark.parametrize("newline", ["\n", "\r\n"], ids=["unix", "windows"])
def test_main(
    git_repo,
    monkeypatch,
    capsys,
    arguments,
    newline,
    pyproject_toml,
    expect_stdout,
    expect_a_py,
    expect_retval,
    root_as_cwd,
    tmp_path_factory,
):
    """Main function outputs diffs and modifies files correctly"""
    if root_as_cwd:
        cwd = git_repo.root
        pwd = Path("")
    else:
        cwd = tmp_path_factory.mktemp("not_a_git_repo")
        pwd = git_repo.root
    monkeypatch.chdir(cwd)
    paths = git_repo.add(
        {
            "pyproject.toml": dedent(pyproject_toml),
            "subdir/a.py": newline,
            "b.py": newline,
        },
        commit="Initial commit",
    )
    paths["subdir/a.py"].write_bytes(newline.join(A_PY).encode("ascii"))
    paths["b.py"].write_bytes(f"print(42 ){newline}".encode("ascii"))

    retval = darker.__main__.main(arguments + [str(pwd / "subdir")])

    stdout = capsys.readouterr().out.replace(str(git_repo.root), "")
    diff_output = stdout.splitlines(False)
    if expect_stdout:
        if "--diff" in arguments:
            assert "\t" in diff_output[0], diff_output[0]
            diff_output[0], old_mtime = diff_output[0].split("\t", 1)
            assert old_mtime.endswith(" +0000")
            assert "\t" in diff_output[1], diff_output[1]
            diff_output[1], new_mtime = diff_output[1].split("\t", 1)
            assert new_mtime.endswith(" +0000")
            assert all("\t" not in line for line in diff_output[2:])
        else:
            assert all("\t" not in line for line in diff_output)
    assert diff_output == expect_stdout
    assert paths["subdir/a.py"].read_bytes().decode("ascii") == newline.join(
        expect_a_py
    )
    assert paths["b.py"].read_bytes().decode("ascii") == f"print(42 ){newline}"
    assert retval == expect_retval

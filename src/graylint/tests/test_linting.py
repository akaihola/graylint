"""Unit tests for `graylint.linting`."""

# pylint: disable=protected-access,too-many-arguments,too-many-positional-arguments
# pylint: disable=use-dict-literal

from __future__ import annotations

import os
from pathlib import Path
from subprocess import PIPE, Popen  # nosec
from textwrap import dedent
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Callable
from unittest.mock import patch

import pytest
from _pytest.fixtures import SubRequest

from darkgraylib.git import WORKTREE, RevisionRange
from darkgraylib.testtools.git_repo_plugin import GitRepoFixture
from darkgraylib.testtools.helpers import raises_if_exception
from darkgraylib.utils import WINDOWS
from graylint import linting
from graylint.command_line import OutputSpec, shlex_split
from graylint.linter_parser.message import INVALID_LINE, LinterMessage, MessageLocation
from graylint.linting import (
    DiffLineMapping,
    make_linter_env,
)
from graylint.tests.testhelpers import SKIP_ON_UNIX, SKIP_ON_WINDOWS

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from contextlib import AbstractContextManager


@pytest.mark.kwparametrize(
    dict(column=0, expect=f"{Path('/path/to/file.py')}:42"),
    dict(column=5, expect=f"{Path('/path/to/file.py')}:42:5"),
)
def test_message_location_str(column, expect):
    """Null column number is hidden from string representation of message location"""
    location = MessageLocation(Path("/path/to/file.py"), 42, column)

    result = str(location)

    assert result == expect


@pytest.mark.kwparametrize(
    dict(
        new_location=("/path/to/new_file.py", 43, 8),
        old_location=("/path/to/old_file.py", 42, 13),
        get_location=("/path/to/new_file.py", 43, 21),
        expect_location=MessageLocation(Path("/path/to/old_file.py"), 42, 21),
    ),
    dict(
        new_location=("/path/to/new_file.py", 43, 8),
        old_location=("/path/to/old_file.py", 42, 13),
        get_location=("/path/to/a_different_file.py", 43, 21),
        expect_location=INVALID_LINE,
    ),
    dict(
        new_location=("/path/to/file.py", 43, 8),
        old_location=("/path/to/file.py", 42, 13),
        get_location=("/path/to/file.py", 42, 21),
        expect_location=INVALID_LINE,
    ),
)
def test_diff_line_mapping_ignores_column(
    new_location, old_location, get_location, expect_location
):
    """Diff location mapping ignores column and attaches column of queried location"""
    mapping = linting.DiffLineMapping()
    new_location_ = MessageLocation(Path(new_location[0]), *new_location[1:])
    old_location = MessageLocation(Path(old_location[0]), *old_location[1:])
    get_location = MessageLocation(Path(get_location[0]), *get_location[1:])

    mapping[new_location_] = old_location
    result = mapping.get(get_location)

    assert result == expect_location


def test_normalize_whitespace():
    """Whitespace runs and leading/trailing whitespace is normalized"""
    description = "module.py:42:  \t  indented message,    trailing spaces and tabs \t "
    message = LinterMessage("mylinter", description)

    result = linting.normalize_whitespace(message)

    assert result == LinterMessage(
        "mylinter", "module.py:42: indented message, trailing spaces and tabs"
    )


@pytest.mark.kwparametrize(
    dict(rev2="master", expect=NotImplementedError),
    dict(rev2=WORKTREE, expect=None),
)
def test_require_rev2_worktree(rev2, expect):
    """``_require_rev2_worktree`` raises an exception if rev2 is not ``WORKTREE``"""
    with raises_if_exception(expect):
        linting._require_rev2_worktree(rev2)


@pytest.mark.kwparametrize(
    dict(cmdline="echo", expect=["first.py the  2nd.py\n"]),
    dict(cmdline="echo words before", expect=["words before first.py the  2nd.py\n"]),
    dict(cmdline='echo "two  spaces"', expect=["two  spaces first.py the  2nd.py\n"]),
    dict(cmdline="echo eat  spaces", expect=["eat spaces first.py the  2nd.py\n"]),
)
def test_check_linter_output(tmp_path, cmdline, expect):
    """``_check_linter_output()`` runs linter and returns the stdout stream"""
    (tmp_path / "first.py").touch()
    (tmp_path / "the  2nd.py").touch()
    with linting._check_linter_output(
        shlex_split(cmdline),
        tmp_path,
        {Path("first.py"), Path("the  2nd.py"), Path("missing.py")},
        make_linter_env(tmp_path, "WORKTREE"),
    ) as stdout:
        lines = list(stdout)

    assert lines == expect


@pytest.fixture(scope="module")
def run_linters_repo(
    request: SubRequest, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[GitRepoFixture]:
    """Git repository fixture for `test_run_linters`."""
    # pylint: disable=no-member  # pylint bug?
    with GitRepoFixture.context(request, tmp_path_factory) as repo:
        paths = repo.add(
            {
                "test.py": "1 unmoved\n2 modify\n3 to 4 moved\n",
                "nonpython.txt": "hello\n",
            },
            commit="Initial commit",
        )
        paths["test.py"].write_bytes(
            b"1 unmoved\n2 modified\n3 inserted\n3 to 4 moved\n"
        )
        yield repo


@pytest.mark.kwparametrize(
    dict(
        # New message for test.py
        messages_after=["test.py:1: new message"],
        expect_output=["", "test.py:1: new message [cat]"],
    ),
    dict(
        # New message for test.py, including column number
        messages_after=["test.py:1:42: new message with column number"],
        expect_output=["", "test.py:1:42: new message with column number [cat]"],
    ),
    dict(
        # Identical message on an unmodified unmoved line in test.py
        messages_before=["test.py:1:42: same message on same line"],
        messages_after=["test.py:1:42: same message on same line"],
    ),
    dict(
        # Identical message on an unmodified moved line in test.py
        messages_before=["test.py:3:42: same message on a moved line"],
        messages_after=["test.py:4:42: same message on a moved line"],
    ),
    dict(
        # Additional message on an unmodified moved line in test.py
        messages_before=["test.py:3:42: same message"],
        messages_after=[
            "test.py:4:42: same message",
            "test.py:4:42: additional message",
        ],
        expect_output=["", "test.py:4:42: additional message [cat]"],
    ),
    dict(
        # Changed message on an unmodified moved line in test.py
        messages_before=["test.py:4:42: old message"],
        messages_after=["test.py:4:42: new message"],
        expect_output=["", "test.py:4:42: new message [cat]"],
    ),
    dict(
        # Identical message but on an inserted line in test.py
        messages_before=["test.py:1:42: same message also on an inserted line"],
        messages_after=[
            "test.py:1:42: same message also on an inserted line",
            "test.py:2:42: same message also on an inserted line",
        ],
        expect_output=["", "test.py:2:42: same message also on an inserted line [cat]"],
    ),
    dict(
        # Warning for a file missing from the working tree
        messages_after=["missing.py:1: a missing Python file"],
        expect_log=["WARNING Missing file missing.py from cat messages"],
    ),
    dict(
        # Linter message for a non-Python file is ignored with a warning
        messages_after=["nonpython.txt:1: non-py"],
        expect_log=[
            "WARNING Linter message for a non-Python file: nonpython.txt:1: non-py"
        ],
    ),
    dict(
        # Message for file outside common root is ignored with a warning (Unix)
        messages_after=["/elsewhere/mod.py:1: elsewhere"],
        expect_log=[
            "WARNING Linter message for a file /elsewhere/mod.py outside root"
            " directory {root}"
        ],
        marks=SKIP_ON_WINDOWS,
    ),
    dict(
        # Message for file outside common root is ignored with a warning (Win)
        messages_after=["C:\\elsewhere\\mod.py:1: elsewhere"],
        expect_log=[
            "WARNING Linter message for a file C:\\elsewhere\\mod.py outside root"
            " directory {root}"
        ],
        marks=SKIP_ON_UNIX,
    ),
    messages_before=[],
    expect_output=[],
    expect_log=[],
)
def test_run_linters(
    run_linters_repo: GitRepoFixture,
    make_temp_copy: Callable[[Path], AbstractContextManager[Path]],
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
    messages_before: list[str],
    messages_after: list[str],
    expect_output: list[str],
    expect_log: list[str],
) -> None:
    """Linter gets correct paths on command line and outputs just changed lines

    We use ``cat`` as our "linter". It just gets the content of the given file.
    What this test does is the equivalent of e.g.::

    - committing a ``test.py`` and a ``messages`` with mock linter output
    - modifying ``test.py`` and ``messages`` in the working tree
    - running::

          $ graylint -L 'cat messages' test.py
          test.py:1: <here are some messages from the test case>

    """
    with make_temp_copy(run_linters_repo.root) as root:
        repo = GitRepoFixture(
            root, {"HOME": str(root), "LC_ALL": "C", "PATH": os.environ["PATH"]}
        )
        paths = repo.add(
            {"messages": "\n".join(messages_before)}, commit="Messages before"
        )
        paths["messages"].write_text("\n".join(messages_after))
        cmdlines: list[list[str]] = [["cat", "messages"]]
        revrange = RevisionRange("HEAD", ":WORKTREE:")

        linting.run_linters(
            cmdlines, repo.root, {Path("dummy path")}, revrange, [OutputSpec("gnu")]
        )

    # We can now verify that the linter received the correct paths on its command line
    # by checking standard output from the our `echo` "linter".
    # The test cases also verify that only linter reports on modified lines are output.
    result = capsys.readouterr().out.splitlines()
    assert result == repo.expand_root(expect_output)
    logs = [
        f"{record.levelname} {record.message}"
        for record in caplog.records
        if record.levelname != "DEBUG"
    ]
    assert logs == repo.expand_root(expect_log)


def test_run_linters_non_worktree():
    """``run_linters()`` doesn't support linting commits, only the worktree"""
    with pytest.raises(NotImplementedError):
        linting.run_linters(
            [["dummy-linter"]],
            Path("/dummy"),
            {Path("dummy.py")},
            RevisionRange.parse_with_common_ancestor(
                "..HEAD", Path("dummy cwd"), stdin_mode=False
            ),
            [OutputSpec("gnu")],
        )


@pytest.fixture(scope="module")
def simple_test_repo(request, tmp_path_factory):
    """Git repository fixture for `test_run_linters`."""
    with GitRepoFixture.context(request, tmp_path_factory) as repo:
        # pylint: disable=no-member  # pylint bug?
        paths = repo.add({"__init__.py": "1\n2\n3\n4\n5\n6\n"}, commit="Initial commit")
        initial = repo.get_hash()
        repo.create_tag("initial")
        paths["__init__.py"].write_bytes(b"a\nb\nc\n4\ne\nf\n")
        yield SimpleNamespace(
            root=repo.root,
            paths=paths,
            hash_initial=initial,
        )


@pytest.mark.parametrize(
    "message, expect",
    [
        ("", 0),
        ("__init__.py:1: message on modified line", 1),
        ("__init__.py:4: message on unmodified line", 0),
    ],
)
def test_run_linters_return_value(simple_test_repo, message, expect):
    """``run_linters()`` returns the number of linter errors on modified lines"""
    cmdline = ["echo", message]

    result = linting.run_linters(
        [cmdline],
        simple_test_repo.root,
        {Path("test.py")},
        RevisionRange("HEAD", ":WORKTREE:"),
        [OutputSpec("gnu")],
    )

    assert result == expect


def test_run_linters_on_new_file(
    simple_test_repo: SimpleNamespace,
    make_temp_copy: Callable[[Path], AbstractContextManager[Path]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``run_linters()`` considers file missing from history as empty

    Passes through all linter errors as if the original file was empty.

    """
    with make_temp_copy(simple_test_repo.root) as root:
        monkeypatch.chdir(root)
        (root / "new_file.py").write_bytes(b"1\n2\n")

        linting.run_linters(
            [["echo", "new_file.py:1: message on a file not seen in Git history"]],
            root,
            {Path("new_file.py")},
            RevisionRange(simple_test_repo.hash_initial, ":WORKTREE:"),
            [OutputSpec("gnu")],
        )

    output = capsys.readouterr().out.splitlines()
    assert output == [
        "",
        "new_file.py:1: message on a file not seen in Git history new_file.py [echo]",
    ]


def test_run_linters_line_separation(
    simple_test_repo: SimpleNamespace,
    make_temp_copy: Callable[[Path], AbstractContextManager[Path]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``run_linters`` separates contiguous blocks of linter output with empty lines"""
    with make_temp_copy(simple_test_repo.root) as root:
        linter_output = root / "dummy-linter-output.txt"
        linter_output.write_text(
            dedent(
                """
                __init__.py:2: first block
                __init__.py:3: of linter output
                __init__.py:5: second block
                __init__.py:6: of linter output
                """
            )
        )
        cat_command = ["cmd", "/c", "type"] if WINDOWS else ["cat"]

        linting.run_linters(
            [[*cat_command, str(linter_output)]],
            root,
            {Path("__init__.py")},
            RevisionRange("HEAD", ":WORKTREE:"),
            [OutputSpec("gnu")],
        )

    result = capsys.readouterr().out
    cat_cmd = "cmd" if WINDOWS else "cat"
    assert result == dedent(
        f"""
        __init__.py:2: first block [{cat_cmd}]
        __init__.py:3: of linter output [{cat_cmd}]

        __init__.py:5: second block [{cat_cmd}]
        __init__.py:6: of linter output [{cat_cmd}]
        """
    )


def test_run_linters_stdin():
    """`linting.run_linters` raises a `NotImplementeError` on ``--stdin-filename``"""
    with pytest.raises(
        NotImplementedError,
        match=r"^The -l/--lint option isn't yet available with --stdin-filename$",
    ):
        # end of test setup

        _ = linting.run_linters(
            [["dummy-linter-command"]],
            Path("/dummy-dir"),
            {Path("dummy.py")},
            RevisionRange("HEAD", ":STDIN:"),
            [OutputSpec("gnu")],
        )


def _build_messages(
    lines_and_messages: Iterable[tuple[int, str] | tuple[int, str, str]],
) -> dict[MessageLocation, list[LinterMessage]]:
    return {
        MessageLocation(Path("a.py"), line, 0): [
            LinterMessage(*msg.split(":")) for msg in msgs
        ]
        for line, *msgs in lines_and_messages
    }


def test_print_new_linter_messages(capsys):
    """`linting._print_new_linter_messages()` hides old intact linter messages"""
    baseline = _build_messages(
        [
            (2, "mypy:single message on an unmodified line"),
            (4, "mypy:single message on a disappearing line"),
            (6, "mypy:single message on a moved line"),
            (8, "mypy:single message on a modified line"),
            (10, "mypy:multiple messages", "pylint:on the same moved line"),
            (
                12,
                "mypy:old message which will be replaced",
                "pylint:on an unmodified line",
            ),
            (14, "mypy:old message on a modified line"),
        ]
    )
    new_messages = _build_messages(
        [
            (2, "mypy:single message on an unmodified line"),
            (5, "mypy:single message on a moved line"),
            (8, "mypy:single message on a modified line"),
            (11, "mypy:multiple messages", "pylint:on the same moved line"),
            (
                12,
                "mypy:new message replacing the old one",
                "pylint:on an unmodified line",
            ),
            (14, "mypy:new message on a modified line"),
            (16, "mypy:multiple messages", "pylint:on the same new line"),
        ]
    )
    diff_line_mapping = DiffLineMapping()
    for new_line, old_line in {2: 2, 5: 6, 11: 10, 12: 12}.items():
        diff_line_mapping[MessageLocation(Path("a.py"), new_line)] = MessageLocation(
            Path("a.py"), old_line
        )

    linting._print_new_linter_messages(
        baseline, new_messages, diff_line_mapping, [OutputSpec("gnu")]
    )

    result = capsys.readouterr().out.splitlines()
    assert result == [
        "",
        "a.py:8: single message on a modified line [mypy]",
        "",
        "a.py:12: new message replacing the old one [mypy]",
        "",
        "a.py:14: new message on a modified line [mypy]",
        "",
        "a.py:16: multiple messages [mypy]",
        "a.py:16: on the same new line [pylint]",
    ]


LINT_EMPTY_LINES_CMD = [
    "python",
    "-c",
    dedent(
        """
        from pathlib import Path
        for path in Path(".").glob("**/*.py"):
            for linenum, line in enumerate(path.open(), start=1):
                if not line.strip():
                    print(f"{path}:{linenum}: EMPTY")
        """
    ),
]

LINT_NONEMPTY_LINES_CMD = [
    "python",
    "-c",
    dedent(
        """
        from pathlib import Path
        for path in Path(".").glob("**/*.py"):
            for linenum, line in enumerate(path.open(), start=1):
                if line.strip():
                    print(f"{path}:{linenum}: {line.strip()}")
        """
    ),
]


def test_get_messages_from_linters_for_baseline(git_repo):
    """Test for `linting._get_messages_from_linters_for_baseline`"""
    git_repo.add({"a.py": "First line\n\nThird line\n"}, commit="Initial commit")
    initial = git_repo.get_hash()
    git_repo.add({"a.py": "Just one line\n"}, commit="Second commit")
    git_repo.create_branch("baseline", initial)

    result = linting._get_messages_from_linters_for_baseline(
        linter_cmdlines=[LINT_EMPTY_LINES_CMD, LINT_NONEMPTY_LINES_CMD],
        root=git_repo.root,
        paths=[Path("a.py"), Path("subdir/b.py")],
        revision="baseline",
    )

    a_py = Path("a.py")
    expect = {
        MessageLocation(a_py, 1): [LinterMessage("python", "First line")],
        MessageLocation(a_py, 2): [LinterMessage("python", "EMPTY")],
        MessageLocation(a_py, 3): [LinterMessage("python", "Third line")],
    }
    assert result == expect


class AssertEmptyStderrPopen(Popen[str]):  # pylint: disable=too-few-public-methods
    """A Popen to use for the following test; asserts that its stderr is empty"""

    def __init__(  # type: ignore[explicit-any]
        self,
        args: list[str],
        **kwargs: Any,  # noqa: ANN401
    ):
        """Initialize the Popen object and assert that its stderr is empty."""
        super().__init__(args, stderr=PIPE, **kwargs)
        assert self.stderr is not None
        assert self.stderr.read() == ""


def test_get_messages_from_linters_for_baseline_no_mypy_errors(simple_test_repo):
    """Ensure Mypy does not fail early when ``__init__.py`` is at the repository root

    Regression test for #498

    """
    with patch.object(linting, "Popen", AssertEmptyStderrPopen):
        # end of test setup

        _ = linting._get_messages_from_linters_for_baseline(
            linter_cmdlines=[["mypy"]],
            root=simple_test_repo.root,
            paths=[Path("__init__.py")],
            revision=simple_test_repo.hash_initial,
        )


@pytest.mark.kwparametrize(
    dict(
        cmdline=[],
        expect=[],
    ),
    dict(
        cmdline=["mypy", "--show-error-codes"],
        expect=["mypy", "--show-error-codes"],
    ),
    dict(
        cmdline=["flake8", "--format=%(path)s:%(row)d:%(col)d: %(text)s"],
        expect=["flake8", "--format=%(path)s:%(row)d:%(col)d: %(text)s"],
    ),
    dict(
        cmdline=["ruff"],
        expect=["ruff", "check", "--output-format=concise"],
    ),
    dict(
        cmdline=["ruff", "check"],
        expect=["ruff", "check", "--output-format=concise"],
    ),
    dict(
        cmdline=["ruff", "--fix"],
        expect=["ruff", "check", "--fix", "--output-format=concise"],
    ),
    dict(
        cmdline=["ruff", "check", "--output-format=json"],
        expect=["ruff", "check", "--output-format=json"],
    ),
    dict(
        # nonsensical case, but we're not doing proper Ruff argument parsing
        cmdline=["ruff", "format"],
        expect=["ruff", "check", "format", "--output-format=concise"],
    ),
)
def test_transform_linter_command(cmdline, expect):
    """_transform_linter_command transforms ruff commands and passes through others."""
    if expect is IndexError:
        with pytest.raises(IndexError):
            linting._transform_linter_command(cmdline)
    else:
        result = linting._transform_linter_command(cmdline)
        assert result == expect


@pytest.mark.kwparametrize(
    dict(
        output=dedent(
            """
            ************* Module src.graylint.linter_parser.gnu
            subdir/first.py:30:0: C0301: Line too long (104/100) (line-too-long)

            ------------------------------------------------------------------
            Your code has been rated at 4.67/10 (previous run: 4.67/10, +0.00)

            """
        ),
        expect_parser="gnu",
        expect_messages={
            MessageLocation(Path("subdir/first.py"), 30, 0): [
                LinterMessage(
                    linter="pylint",
                    description="C0301: Line too long (104/100) (line-too-long)",
                )
            ],
        },
    ),
)
def test_parse_linter_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    output: str,
    expect_parser: str,
    expect_messages: dict[MessageLocation, list[LinterMessage]],
) -> None:
    """Test that the correct plugin is used and parses messages correctly."""
    monkeypatch.chdir(tmp_path)
    Path("subdir").mkdir()
    Path("subdir/first.py").touch()
    Path("subdir/second.py").touch()
    (result, parser) = linting.parse_linter_output(["pylint"], output, Path(), set())

    assert parser.name == expect_parser
    assert result == expect_messages

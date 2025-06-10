"""Run arbitrary linters on given files in a Git repository

This supports any linter which reports on standard output and has a fairly standard
correct output format::

    <path>:<linenum>: <description>
    <path>:<linenum>:<column>: <description>

For example, Mypy outputs::

    module.py:57: error: Function is missing a type annotation for one or more arguments

Pylint, on the other hand::

    module.py:44:8: R1720: Unnecessary "elif" after "raise" (no-else-raise)

All such output from the linter will be printed on the standard output
provided that the ``<linenum>`` falls on a changed line.

"""

from __future__ import annotations

import logging
import os
import re
import shlex
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from subprocess import PIPE, Popen  # nosec
from tempfile import TemporaryDirectory
from typing import (
    IO,
    TYPE_CHECKING,
    Callable,
    Collection,
    Generator,
    Iterable,
    Sequence,
)

from darkgraylib.diff import map_unmodified_lines
from darkgraylib.git import (
    STDIN,
    WORKTREE,
    RevisionRange,
    git_clone_local,
    git_get_content_at_revision,
    git_get_root,
    git_rev_parse,
)
from graylint.output.plugin_helpers import create_output_plugins

if TYPE_CHECKING:
    from graylint.command_line import OutputSpec

logger = logging.getLogger(__name__)


@dataclass(eq=True, frozen=True, order=True)
class MessageLocation:
    """A file path, line number and column number for a linter message

    Line and column numbers a 0-based, and zero is used for an unspecified column, and
    for the non-specified location.

    """

    path: Path
    line: int
    column: int = 0

    def __str__(self) -> str:
        """Convert file path, line and column into a linter line prefix string

        :return: Either ``"path:line:column"`` or ``"path:line"`` (if column is zero)

        """
        if self.column:
            return f"{self.path}:{self.line}:{self.column}"
        return f"{self.path}:{self.line}"


NO_MESSAGE_LOCATION = MessageLocation(Path(""), 0, 0)


@dataclass
class LinterMessage:
    """Information about a linter message"""

    linter: str
    description: str


class DiffLineMapping:
    """A mapping from unmodified lines in new and old versions of files"""

    def __init__(self) -> None:
        self._mapping: dict[tuple[Path, int], tuple[Path, int]] = {}

    def __setitem__(
        self, new_location: MessageLocation, old_location: MessageLocation
    ) -> None:
        """Add a pointer from new to old line to the mapping

        :param new_location: The file path and linenum of the message in the new version
        :param old_location: The file path and linenum of the message in the old version

        """
        self._mapping[new_location.path, new_location.line] = (
            old_location.path,
            old_location.line,
        )

    def get(self, new_location: MessageLocation) -> MessageLocation:
        """Get the old location of the message based on the mapping

        The mapping is between line numbers, so the column number of the message in the
        new file is injected into the corresponding location in the old version of the
        file.

        :param new_location: The path, line and column number of a linter message in the
                             new version of a file
        :return: The path, line and column number of the same message in the old version
                 of the file

        """
        key = (new_location.path, new_location.line)
        if key in self._mapping:
            (old_path, old_line) = self._mapping[key]
            return MessageLocation(old_path, old_line, new_location.column)
        return NO_MESSAGE_LOCATION


def normalize_whitespace(message: LinterMessage) -> LinterMessage:
    """Given a line of linter output, shortens runs of whitespace to a single space

    Also removes any leading or trailing whitespace.

    This is done to support comparison of different ``cov_to_lint.py`` runs. To make the
    output more readable and compact, the tool adjusts whitespace. This is done to both
    align runs of lines and to remove blocks of extra indentation. For differing sets of
    coverage messages from ``pytest-cov`` runs of different versions of the code, these
    whitespace adjustments can differ, so we need to normalize them to compare and match
    them.

    :param message: The linter message to normalize
    :return: The normalized linter message with leading and trailing whitespace stripped
             and runs of whitespace characters collapsed into single spaces

    """
    return LinterMessage(
        message.linter, re.sub(r"\s\s+", " ", message.description).strip()
    )


def make_linter_env(root: Path, revision: str) -> dict[str, str]:
    """Populate environment variables for running linters

    :param root: The path to the root of the Git repository
    :param revision: The commit hash of the Git revision being linted, or ``"WORKTREE"``
                     if the working tree is being linted
    :return: The environment variables dictionary to pass to the linter

    """
    return {
        **os.environ,
        "GRAYLINT_ORIG_REPO": str(root),
        "GRAYLINT_REV_COMMIT": ("WORKTREE" if revision == "WORKTREE" else revision[:7]),
    }


def _strict_nonneg_int(text: str) -> int:
    """Strict parsing of strings to non-negative integers

    Allow no leading or trailing whitespace, nor plus or minus signs.

    :param text: The string to convert
    :raises ValueError: Raises if the string has any non-numeric characters
    :return: [description]
    :rtype: [type]
    """
    if text.strip("+-\t ") != text:
        raise ValueError(r"invalid literal for int() with base 10: {text}")
    return int(text)


def _parse_linter_line(
    linter: str, line: str, cwd: Path
) -> tuple[MessageLocation, LinterMessage]:
    """Parse one line of linter output

    Only parses lines with
    - a relative or absolute file path (without leading-trailing whitespace),
    - a non-negative line number (without leading/trailing whitespace),
    - optionally a column number (without leading/trailing whitespace), and
    - a description.

    Examples of successfully parsed lines::

        path/to/file.py:42: Description
        /absolute/path/to/file.py:42:5: Description

    Given ``cwd=Path("/absolute")``, these would be parsed into::

        (Path("path/to/file.py"), 42, "path/to/file.py:42:", "Description")
        (Path("path/to/file.py"), 42, "path/to/file.py:42:5:", "Description")

    For all other lines, a dummy entry is returned: an empty path, zero as the line
    number, an empty location string and an empty description. Such lines should be
    simply ignored, since many linters display supplementary information insterspersed
    with the actual linting notifications.

    :param linter: The name of the linter
    :param line: The linter output line to parse. May have a trailing newline.
    :param cwd: The directory in which the linter was run, and relative to which paths
                are returned
    :return: A 2-tuple of
             - the file path, line and column numbers of the linter message, and
             - the linter name and message description.

    """
    try:
        location, description = line.rstrip().split(": ", 1)
        if location[1:3] == ":\\":
            # Absolute Windows paths need special handling. Separate out the ``C:`` (or
            # similar), then split by colons, and finally re-insert the ``C:``.
            path_in_drive, linenum_str, *rest = location[2:].split(":")
            path_str = f"{location[:2]}{path_in_drive}"
        else:
            path_str, linenum_str, *rest = location.split(":")
        if path_str.strip() != path_str:
            raise ValueError(r"Filename {path_str!r} has leading/trailing whitespace")
        linenum = _strict_nonneg_int(linenum_str)
        if len(rest) > 1:
            raise ValueError("Too many colon-separated tokens in {location!r}")
        if len(rest) == 1:
            # Make sure the column looks like an int in "<path>:<linenum>:<column>"
            column = _strict_nonneg_int(rest[0])  # noqa: F841
        else:
            column = 0
    except ValueError:
        # Encountered a non-parsable line which doesn't express a linting error.
        # For example, on Mypy:
        # "Found XX errors in YY files (checked ZZ source files)"
        # "Success: no issues found in 1 source file"
        logger.debug("Unparsable linter output: %s", line[:-1])
        return (NO_MESSAGE_LOCATION, LinterMessage(linter, ""))
    path = Path(path_str)
    if path.is_absolute():
        try:
            path = path.relative_to(cwd)
        except ValueError:
            logger.warning(
                "Linter message for a file %s outside root directory %s",
                path_str,
                cwd,
            )
            return (NO_MESSAGE_LOCATION, LinterMessage(linter, ""))
    return (MessageLocation(path, linenum, column), LinterMessage(linter, description))


def _require_rev2_worktree(rev2: str) -> None:
    """Exit with an error message if ``rev2`` is not ``WORKTREE``

    This is used when running linters since linting arbitrary commits is not supported.

    :param rev2: The ``rev2`` revision to lint.

    """
    if rev2 != WORKTREE:
        raise NotImplementedError(
            "Linting arbitrary commits is not supported. "
            "Please use -r {<rev>|<rev>..|<rev>...} instead."
        )


@contextmanager
def _check_linter_output(
    cmdline: list[str],
    root: Path,
    paths: Collection[Path],
    env: dict[str, str],
) -> Generator[IO[str]]:
    """Run a linter as a subprocess and return its standard output stream

    :param cmdline: The command line for running the linter
    :param root: The common root of all files to lint
    :param paths: Paths of files to check, relative to ``root``
    :param env: Environment variables to pass to the linter
    :return: The standard output stream of the linter subprocess

    """
    existing_path_strs = sorted(str(path) for path in paths if (root / path).exists())
    cmdline_and_paths = cmdline + existing_path_strs
    logger.debug("[%s]$ %s", root, shlex.join(cmdline_and_paths))
    with Popen(  # nosec
        cmdline_and_paths,
        stdout=PIPE,
        encoding="utf-8",
        cwd=root,
        env=env,
    ) as linter_process:
        # condition needed for MyPy (see https://stackoverflow.com/q/57350490/15770)
        if linter_process.stdout is None:
            raise RuntimeError("Stdout piping failed")
        yield linter_process.stdout


def _transform_linter_command(cmdline: list[str]) -> list[str]:
    """Transform the linter command to ensure required options are in place.

    This is done for ergonomics: The user can just specify ``--lint=ruff`` and have
    ``ruff check --output-format=concise`` run.

    :param cmdline: The command line to transform
    :return: The transformed command line as a list of arguments

    """
    if not cmdline or cmdline[0] != "ruff":
        return cmdline
    transformed_cmdline = cmdline.copy()
    if "check" not in transformed_cmdline:
        transformed_cmdline.insert(1, "check")
    if not any(arg.startswith("--output-format") for arg in transformed_cmdline):
        transformed_cmdline.append("--output-format=concise")
    return transformed_cmdline


def run_linter(  # pylint: disable=too-many-locals
    cmdline: list[str],
    root: Path,
    paths: Collection[Path],
    env: dict[str, str],
) -> dict[MessageLocation, LinterMessage]:
    """Run the given linter and return linting errors falling on changed lines

    :param cmdline: The command line for running the linter
    :param root: The common root of all files to lint
    :param paths: Paths of files to check, relative to ``root``
    :param env: Environment variables to pass to the linter
    :return: The number of modified lines with linting errors from this linter

    """
    missing_files = set()
    result = {}
    transformed_cmdline = _transform_linter_command(cmdline)
    linter = transformed_cmdline[0]
    cmdline_str = shlex.join(transformed_cmdline)
    # 10. run a linter subprocess for files mentioned on the command line which may be
    #     modified or unmodified, to get current linting status in the working tree
    #     (steps 10.-12. are optional)
    with _check_linter_output(transformed_cmdline, root, paths, env) as linter_stdout:
        for line in linter_stdout:
            (location, message) = _parse_linter_line(linter, line, root)
            if location is NO_MESSAGE_LOCATION or location.path in missing_files:
                continue
            if location.path.suffix != ".py":
                logger.warning(
                    "Linter message for a non-Python file: %s: %s",
                    location,
                    message.description,
                )
                continue
            if not location.path.is_file() and not location.path.is_symlink():
                logger.warning("Missing file %s from %s", location.path, cmdline_str)
                missing_files.add(location.path)
                continue
            result[location] = message
    return result


def run_linters(
    linter_cmdlines: list[list[str]],
    root: Path,
    paths: set[Path],
    revrange: RevisionRange,
    output_spec: Sequence[OutputSpec],
) -> int:
    """Run the given linters on a set of files in the repository, filter messages

    Linter message filtering works by

    - running linters once in ``rev1`` to establish a baseline,
    - running them again in ``rev2`` to get linter messages after user changes, and
    - printing out only new messages which were not present in the baseline.

    If the source tree is not a Git repository, a baseline is not used, and all linter
    messages are printed

    :param linter_cmdlines: The command lines for linter tools to run on the files
    :param root: The root of the relative paths
    :param paths: The files and directories to check, relative to ``root``
    :param revrange: The Git revisions to compare
    :param output_spec: The output formats and destinations for linter messages
    :raises NotImplementedError: if ``--stdin-filename`` is used
    :return: Total number of linting errors found on modified lines

    """
    if not linter_cmdlines:
        return 0
    if revrange.rev2 == STDIN:
        raise NotImplementedError(
            "The -l/--lint option isn't yet available with --stdin-filename"
        )
    _require_rev2_worktree(revrange.rev2)
    git_root = git_get_root(root)
    if not git_root:
        # In a non-Git root, don't use a baseline
        messages = _get_messages_from_linters(
            linter_cmdlines,
            root,
            paths,
            make_linter_env(root, "WORKTREE"),
        )
        return _print_new_linter_messages(
            baseline={},
            new_messages=messages,
            diff_line_mapping=DiffLineMapping(),
            output_spec=output_spec,
        )
    git_paths = {(root / path).relative_to(git_root) for path in paths}
    # 10. first do a temporary checkout at `rev1` and run linter subprocesses once for
    #     all files which are mentioned on the command line to establish a baseline
    #     (steps 10.-12. are optional)
    baseline = _get_messages_from_linters_for_baseline(
        linter_cmdlines,
        git_root,
        git_paths,
        revrange.rev1,
    )
    messages = _get_messages_from_linters(
        linter_cmdlines,
        git_root,
        git_paths,
        make_linter_env(git_root, "WORKTREE"),
    )
    files_with_messages = {location.path for location in messages}
    # 11. create a mapping from line numbers of unmodified lines in the current versions
    #     to corresponding line numbers in ``rev1``
    diff_line_mapping = _create_line_mapping(git_root, files_with_messages, revrange)
    # 12. hide linter messages which appear in the current versions and identically on
    #     corresponding lines in ``rev1``, and show all other linter messages
    return _print_new_linter_messages(
        baseline, messages, diff_line_mapping, output_spec
    )


def _identity_line_processor(message: LinterMessage) -> LinterMessage:
    """Return message unmodified in the default line processor

    :param message: The original message
    :return: The unmodified message

    """
    return message


def _get_messages_from_linters(
    linter_cmdlines: Iterable[list[str]],
    root: Path,
    paths: Collection[Path],
    env: dict[str, str],
    line_processor: Callable[[LinterMessage], LinterMessage] = _identity_line_processor,
) -> dict[MessageLocation, list[LinterMessage]]:
    """Run given linters for the given directory and return linting errors

    :param linter_cmdlines: The command lines for running the linters
    :param root: The common root of all files to lint
    :param paths: Paths of files to check, relative to ``root``
    :param env: The environment variables to pass to the linter
    :param line_processor: Pre-processing callback for linter output lines
    :return: Linter messages

    """
    result = defaultdict(list)
    for cmdline in linter_cmdlines:
        for message_location, message in run_linter(cmdline, root, paths, env).items():
            result[message_location].append(line_processor(message))
    return result


def _log_messages(
    baseline: dict[MessageLocation, list[LinterMessage]],
    new_messages: dict[MessageLocation, list[LinterMessage]],
) -> None:
    """Output recorded messages at baseline and at rev2 to debug log, no highlighting

    :param baseline: The baseline messages recorded for revision ``rev1``
    :param new_messages: The new messages recorded for revision ``rev2``

    """
    for title, message_set in [
        ("BASELINE AT REV1", baseline),
        ("CURRENT AT REV2", new_messages),
    ]:
        logger.debug("%s:", title)
        logger.debug(len(title) * "=")
        for message_location, messages in sorted(message_set.items()):
            for message in messages:
                logger.debug(
                    "%s: %s [%s]", message_location, message.description, message.linter
                )


def _print_new_linter_messages(
    baseline: dict[MessageLocation, list[LinterMessage]],
    new_messages: dict[MessageLocation, list[LinterMessage]],
    diff_line_mapping: DiffLineMapping,
    output_spec: Sequence[OutputSpec],
) -> int:
    """Print all linter messages except those same as before on unmodified lines

    :param baseline: Linter messages and their locations for a previous version
    :param new_messages: New linter messages in a new version of the source file
    :param diff_line_mapping: Mapping between unmodified lines in old and new versions
    :param output_spec: The output formats and destinations for linter messages
    :return: The number of linter errors displayed

    """
    if logger.getEffectiveLevel() <= logging.DEBUG:
        _log_messages(baseline, new_messages)
    error_count = 0
    prev_location = NO_MESSAGE_LOCATION
    with create_output_plugins(output_spec) as outputs:
        for message_location, messages in sorted(new_messages.items()):
            old_location = diff_line_mapping.get(message_location)
            is_modified_line = old_location == NO_MESSAGE_LOCATION
            old_messages: list[LinterMessage] = baseline.get(old_location, [])
            for message in messages:
                if (
                    not is_modified_line
                    and normalize_whitespace(message) in old_messages
                ):
                    # Only hide messages when
                    # - they occurred previously on the corresponding line
                    # - the line hasn't been modified
                    continue
                group_boundary = (
                    message_location.path != prev_location.path
                    or message_location.line > prev_location.line + 1
                )
                prev_location = message_location
                for output in outputs:
                    if group_boundary:
                        output.group_delimiter()
                    output.output(message_location, message)
                error_count += 1
    return error_count


def _get_messages_from_linters_for_baseline(
    linter_cmdlines: list[list[str]],
    root: Path,
    paths: Collection[Path],
    revision: str,
) -> dict[MessageLocation, list[LinterMessage]]:
    """Clone the Git repository at a given revision and run linters against it

    :param linter_cmdlines: The command lines for linter tools to run on the files
    :param root: The root of the Git repository
    :param paths: The files and directories to check, relative to ``root``
    :param revision: The revision to check out
    :return: Linter messages

    """
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "baseline-revision" / root.name
        with git_clone_local(root, revision, tmp_path) as clone_root:
            rev1_commit = git_rev_parse(revision, root)
            result = _get_messages_from_linters(
                linter_cmdlines,
                clone_root,
                paths,
                make_linter_env(root, rev1_commit),
                normalize_whitespace,
            )
    return result


def _create_line_mapping(
    root: Path, files_with_messages: Iterable[Path], revrange: RevisionRange
) -> DiffLineMapping:
    """Create a mapping from unmodified lines in new files to same lines in old versions

    :param root: The root of the repository
    :param files_with_messages: Paths to files which have linter messages
    :param revrange: The revisions to compare
    :return: A dict which maps the line number of each unmodified line in the new
             versions of files to corresponding line numbers in old versions of the same
             files

    """
    diff_line_mapping = DiffLineMapping()
    for path in files_with_messages:
        doc1 = git_get_content_at_revision(path, revrange.rev1, root)
        doc2 = git_get_content_at_revision(path, revrange.rev2, root)
        for linenum2, linenum1 in map_unmodified_lines(doc1, doc2).items():
            location1 = MessageLocation(path, linenum1)
            location2 = MessageLocation(path, linenum2)
            diff_line_mapping[location2] = location1
    return diff_line_mapping

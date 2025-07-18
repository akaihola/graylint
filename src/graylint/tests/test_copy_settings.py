"""Tests for the ``--copy-settings`` CLI argument."""

import logging
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from darkgraylib.command_line import parse_command_line
from darkgraylib.git import RevisionRange
from darkgraylib.testtools.git_repo_plugin import GitRepoFixture
from graylint.__main__ import main_with_error_handling
from graylint.command_line import make_argument_parser
from graylint.config import GraylintConfig
from graylint.copy_settings import CopySettingsStorage
from graylint.linting import run_linters


def test_copy_settings_e2e_ignore_error(
    git_repo: GitRepoFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An end-to-end test to ensure settings are copied and used."""
    monkeypatch.chdir(git_repo.root)
    git_repo.add(
        {
            "pyproject.toml": textwrap.dedent(
                """
                [tool.ruff]
                select = ["F"]
                """
            ),
            "a.py": "import sys",
        },
        commit="Initial commit",
    )
    git_repo.add({"a.py": "import sys\nimport os"}, commit="Add os import")
    pyproject_toml_path = git_repo.root / "pyproject.toml"
    pyproject_toml_path.write_text(
        pyproject_toml_path.read_text()
        + textwrap.dedent(
            """
            [tool.ruff.lint.per-file-ignores]
            "a.py" = ["F401"]
            """
        )
    )

    # We expect exit code 0, because the F401 error in the old revision of a.py is
    # ignored due to the new pyproject.toml being copied to the baseline worktree.
    # The new revision of a.py has no errors.
    return_code = main_with_error_handling(
        [
            "--copy-settings",
            "pyproject.toml",
            "--lint",
            "ruff check .",
            "--revision",
            "HEAD",
            ".",
        ]
    )

    assert return_code == 0


def test_copy_settings_e2e_new_rule(
    git_repo: GitRepoFixture,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A new rule is enabled, but the code is not changed.

    The new rule is violated by the code. Without ``--copy-settings``, a linter error
    would be reported. With ``--copy-settings``, the new rule is also applied to the
    baseline, so no differences are reported.

    """
    monkeypatch.chdir(git_repo.root)
    git_repo.add(
        {
            "pyproject.toml": textwrap.dedent(
                """
                [tool.ruff]
                select = ["F"]
                """
            ),
            "a.py": "import sys  ",
        },
        commit="Initial commit",
    )
    # In the new revision of the worktree, we just enable a new ruff rule.
    pyproject_toml_path = git_repo.root / "pyproject.toml"
    pyproject_toml_path.write_text(
        pyproject_toml_path.read_text().replace(
            'select = ["F"]', 'select = ["F", "W291"]'
        )
    )

    # First, without --copy-settings, we should see a linter error.
    return_code_without_copy = main_with_error_handling(
        [
            "--lint",
            "ruff check .",
            "--revision",
            "HEAD",
            ".",
        ]
    )
    assert return_code_without_copy == 1
    outerr = capsys.readouterr()
    assert "W291" in outerr.out

    # We expect exit code 0, because the E999 error in the new revision of a.py is
    # also present in the old revision of a.py, because the new pyproject.toml is
    # copied to the baseline worktree.
    return_code_with_copy = main_with_error_handling(
        [
            "--copy-settings",
            "pyproject.toml",
            "--lint",
            "ruff check .",
            "--revision",
            "HEAD",
            ".",
        ]
    )

    assert return_code_with_copy == 0


def test_copy_settings_storage_load_files(tmp_path: Path) -> None:
    """Test that CopySettingsStorage loads files correctly."""
    storage = CopySettingsStorage()
    file1 = tmp_path / "file1.txt"
    file1.write_text("content1")
    file2 = tmp_path / "file2.txt"
    file2.write_text("content2")

    storage.load_files(tmp_path, ["file1.txt", "file2.txt"])

    contents = storage.get_all_contents()
    expected_file_count = 2
    assert len(contents) == expected_file_count
    assert contents["file1.txt"] == "content1"
    assert contents["file2.txt"] == "content2"


def test_copy_settings_storage_missing_file(caplog: pytest.LogCaptureFixture) -> None:
    """Test that CopySettingsStorage handles missing files gracefully."""
    caplog.set_level(logging.WARNING)
    storage = CopySettingsStorage()
    storage.load_files(Path(), ["nonexistent.txt"])
    assert not storage.get_all_contents()
    assert "Settings file not found: nonexistent.txt" in caplog.text


def test_copy_settings_argument_parsing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that the --copy-settings argument is parsed correctly."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dummy.py").touch()
    args, _, _ = parse_command_line(
        make_argument_parser,
        ["--copy-settings", "settings.txt", "."],
        "graylint",
        GraylintConfig,
    )
    assert args.copy_settings == ["settings.txt"]


def test_copy_settings_short_argument_parsing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that the -S argument is parsed correctly."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dummy.py").touch()
    args, _, _ = parse_command_line(
        make_argument_parser,
        ["-S", "settings.txt", "."],
        "graylint",
        GraylintConfig,
    )
    assert args.copy_settings == ["settings.txt"]


def test_copy_settings_git_integration(
    git_repo: GitRepoFixture, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that settings files are copied to the baseline worktree."""
    caplog.set_level(logging.DEBUG)
    git_repo.add(
        {
            "pyproject.toml": "[tool.graylint]\n",
            "settings.cfg": "settings content",
        },
        commit="Initial commit",
    )
    git_repo.add({"a.py": "import os"}, commit="Second commit")

    storage = CopySettingsStorage()
    storage.load_files(git_repo.root, ["settings.cfg"])

    with patch("graylint.linting._get_messages_from_linters") as mock_get_messages:
        mock_get_messages.return_value = {}
        run_linters(
            [["echo"]],
            git_repo.root,
            {Path("a.py")},
            RevisionRange("HEAD", ":WORKTREE:"),
            [],
            storage,
        )

    assert "Copied settings file to worktree:" in caplog.text
    assert "settings.cfg" in caplog.text

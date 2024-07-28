# pylint: disable=too-many-arguments,too-many-locals,use-dict-literal

"""Unit tests for :mod:`graylint.command_line`."""

import os
from typing import Literal
from unittest.mock import patch

import pytest

from darkgraylib.command_line import parse_command_line
from darkgraylib.testtools.helpers import raises_if_exception
from graylint.command_line import make_argument_parser
from graylint.config import GraylintConfig


@pytest.mark.kwparametrize(
    dict(require_src=False, expect=[]),
    dict(require_src=True, expect=SystemExit),
)
def test_make_argument_parser(require_src, expect):
    """Parser from ``make_argument_parser()`` fails if src required but not provided."""
    parser = make_argument_parser(require_src)
    with raises_if_exception(expect):

        args = parser.parse_args([])

        assert args.src == expect


@pytest.mark.kwparametrize(
    dict(
        argv=["."],
        expect_value=("lint", []),
        expect_config=("lint", []),
        expect_modified=("lint", ...),
    ),
    dict(
        argv=["-L", "pylint", "."],
        expect_value=("lint", ["pylint"]),
        expect_config=("lint", ["pylint"]),
        expect_modified=("lint", ["pylint"]),
    ),
    dict(
        argv=["--lint", "flake8", "-L", "mypy", "."],
        expect_value=("lint", ["flake8", "mypy"]),
        expect_config=("lint", ["flake8", "mypy"]),
        expect_modified=("lint", ["flake8", "mypy"]),
    ),
)
def test_parse_command_line(
    tmp_path,
    monkeypatch,
    argv,
    expect_value,
    expect_config,
    expect_modified,
):
    """``parse_command_line()`` parses options correctly."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "dummy.py").touch()
    (tmp_path / "my.cfg").touch()
    (tmp_path / "subdir_with_config").mkdir()
    (tmp_path / "subdir_with_config" / "pyproject.toml").touch()
    with patch.dict(os.environ, {}, clear=True), raises_if_exception(
        expect_value,
    ) as expect_exception:

        args, effective_cfg, modified_cfg = parse_command_line(
            make_argument_parser,
            argv,
            "graylint",
            GraylintConfig,
        )

    if not expect_exception:
        arg_name, expect_arg_value = expect_value
        assert getattr(args, arg_name) == expect_arg_value

        option: Literal["lint"]
        option, expect_config_value = expect_config
        if expect_config_value is ...:
            assert option not in effective_cfg
        else:
            assert effective_cfg[option] == expect_config_value

        modified_option: Literal["lint"]
        modified_option, expect_modified_value = expect_modified
        if expect_modified_value is ...:
            assert modified_option not in modified_cfg
        else:
            assert modified_cfg[modified_option] == expect_modified_value

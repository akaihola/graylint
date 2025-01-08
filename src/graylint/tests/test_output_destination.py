"""Tests for `graylint.output.destination.OutputDestination`."""

import sys
from pathlib import Path

import pytest

from darkgraylib.testtools.helpers import raises_if_exception
from graylint.output.destination import OutputDestination


@pytest.mark.kwparametrize(
    dict(
        path_or_dash=Path("-"),
        expect_name=sys.stdout.name,
        expect_mode=sys.stdout.mode,  # pylint: disable=no-member
    ),
    dict(path_or_dash=Path("test.txt"), expect_name="test.txt", expect_mode="w"),
    dict(path_or_dash="invalid", expect_name=TypeError, expect_mode=TypeError),
)
def test_open(tmp_path, monkeypatch, path_or_dash, expect_name, expect_mode):
    """OutputDestination.open() returns a file object for writing."""
    monkeypatch.chdir(tmp_path)
    destination = OutputDestination(path_or_dash)

    with raises_if_exception(expect_name):
        result = destination.open()

        expect_attrs = (expect_name, False, expect_mode)
        assert (result.name, result.closed, result.mode) == expect_attrs


@pytest.mark.kwparametrize(
    dict(path_or_dash="-", expect=False),
    dict(path_or_dash="test.txt", expect=True),
)
def test_close(tmp_path, monkeypatch, path_or_dash, expect):
    """OutputDestination.close() closes the stream as expected."""
    monkeypatch.chdir(tmp_path)
    destination = OutputDestination(Path(path_or_dash))
    stream = destination.open()

    with raises_if_exception(expect):
        destination.close()

    assert stream.closed == expect


@pytest.mark.kwparametrize(
    dict(
        left=OutputDestination(Path("-")),
        right=OutputDestination(Path("-")),
        expect=True,
    )
)
def test_equality(left, right, expect):
    """OutputDestination instances are equal if their destinations are equal."""
    equality = left == right
    assert equality == expect

"""Helpers for using linter parser plugins."""

from __future__ import annotations

import sys
from importlib.metadata import EntryPoint, entry_points
from typing import TYPE_CHECKING, cast

from darkgraylib.plugins import (
    create_plugin,
    get_entry_point_names,
)

if TYPE_CHECKING:
    from graylint.linter_parser.base import LinterParser

ENTRY_POINT_GROUP = "graylint.linter_parser"


def get_linter_parser_entry_points() -> tuple[EntryPoint, ...]:
    """Get the entry points of all built-in linter parser plugins."""
    if sys.version_info < (3, 10):
        return tuple(entry_points()[ENTRY_POINT_GROUP])
    result = entry_points(group=ENTRY_POINT_GROUP)
    return cast("tuple[EntryPoint, ...]", result)


def create_linter_parser_plugins() -> list[LinterParser]:
    """Create and manage multiple linter parser plugins as context managers.

    :output_spec: List of linter parser names to create plugins for
    :return: List of initialized linter parser objects

    """
    return [
        cast("LinterParser", create_plugin(ENTRY_POINT_GROUP, name))
        for name in get_entry_point_names(ENTRY_POINT_GROUP)
    ]

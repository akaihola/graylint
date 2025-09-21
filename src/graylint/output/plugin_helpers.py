"""Helpers for using output format plugins."""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from typing import TYPE_CHECKING, cast

from darkgraylib.plugins import create_plugin

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from graylint.command_line import OutputSpec
    from graylint.output.base import OutputPlugin


OUTPUT_FORMAT_GROUP = "graylint.output_format"


def create_output_plugin(spec: OutputSpec) -> OutputPlugin:
    """Create an output plugin based on the specification."""
    plugin = create_plugin(
        OUTPUT_FORMAT_GROUP, spec.format, spec.path, use_color=spec.use_color
    )
    return cast("OutputPlugin", plugin)


@contextmanager
def create_output_plugins(
    output_spec: Sequence[OutputSpec],
) -> Generator[list[OutputPlugin]]:
    """Create and manage multiple output plugins as context managers.

    :output_spec: List of output specifications to create plugins for
    :return: List of initialized output plugin objects

    """
    with ExitStack() as stack:
        outputs = [
            stack.enter_context(create_output_plugin(output)) for output in output_spec
        ]
        yield outputs

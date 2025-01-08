"""Built-in output format plugins."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from darkgraylib.plugins import create_plugin

if TYPE_CHECKING:
    from graylint.command_line import OutputSpec
    from graylint.output.base import OutputPlugin


OUTPUT_FORMAT_GROUP = "graylint.output_format"


def create_output_plugin(spec: OutputSpec) -> OutputPlugin:
    """Create an output plugin based on the specification."""
    plugin = create_plugin(
        OUTPUT_FORMAT_GROUP, spec.format, spec.path, use_color=spec.use_color
    )
    return cast("OutputPlugin", plugin)

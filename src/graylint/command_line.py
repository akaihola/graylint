"""Command line parsing for the ``graylint`` binary"""

from __future__ import annotations

from argparse import Action, ArgumentParser, Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import darkgraylib.command_line
from darkgraylib.plugins import get_entry_point_names
from graylint import help as hlp
from graylint.output.destination import OutputDestination
from graylint.output.plugin_helpers import OUTPUT_FORMAT_GROUP
from graylint.version import __version__


class ExtendFromEmptyAction(Action):
    """Action to replace a default list with values from the command line."""

    def __call__(
        self,
        parser: ArgumentParser,  # noqa: ARG002
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        """Return items from command line or the default list if omitted."""
        if not isinstance(values, Sequence):
            message = "Expected a sequence of values"
            raise TypeError(message)
        items = [] if option_string else self.default
        items.extend(values)
        setattr(namespace, self.dest, items)


@dataclass
class OutputSpec:
    """Specification for an output format."""

    format: str
    path: OutputDestination = field(
        default_factory=lambda: OutputDestination(Path("-"))
    )
    use_color: bool = False

    @classmethod
    def parse(cls, value: str) -> OutputSpec:
        """Parse a format specification string into a FormatSpec object."""
        if ":" in value:
            fmt, path_str = value.split(":", 1)
        else:
            fmt, path_str = value, "-"

        if fmt not in get_entry_point_names(OUTPUT_FORMAT_GROUP):
            message = f"Unknown output format: {fmt}"
            raise ValueError(message)

        return cls(fmt, OutputDestination(Path(path_str)))

    def with_color(self, *, use_color: bool) -> OutputSpec:
        """Return a copy with color output enabled or disabled."""
        return OutputSpec(self.format, self.path, use_color)


def parse_format_args(value: str) -> list[OutputSpec]:
    """Parse comma-separated format specifications."""
    return [OutputSpec.parse(v.strip()) for v in value.split(",")]


def make_argument_parser(require_src: bool) -> ArgumentParser:
    """Create the argument parser object

    :param require_src: ``True`` to require at least one path as a positional argument
                        on the command line. ``False`` to not require on.

    """
    parser = darkgraylib.command_line.make_argument_parser(
        require_src,
        "Graylint",
        hlp.DESCRIPTION,
        "Read Graylint configuration from `PATH`. Note that linters run by Graylint"
        " won't read this configuration file.",
        __version__,
    )

    parser.add_argument(
        "-L", "--lint", action="append", metavar="CMD", default=[], help=hlp.LINT
    )
    output_formats = get_entry_point_names(OUTPUT_FORMAT_GROUP)
    default_output_format = output_formats[0]
    output_format_names = ", ".join(
        f"{name} (default)" if name == default_output_format else name
        for name in output_formats
    )
    parser.add_argument(
        "-o",
        "--output-format",
        action=ExtendFromEmptyAction,
        type=parse_format_args,
        metavar="<FORMAT[:PATH]>",
        default=[OutputSpec("gnu", OutputDestination(Path("-")))],
        help=hlp.FORMAT_TEMPLATE.format(output_format_names=output_format_names),
    )
    return parser

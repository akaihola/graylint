"""Command line parsing for the ``graylint`` binary"""

from __future__ import annotations

from argparse import Action, ArgumentParser, Namespace
from typing import Any, Sequence

import darkgraylib.command_line
from graylint import help as hlp
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
    return parser

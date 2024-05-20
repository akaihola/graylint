"""Command line parsing for the ``graylint`` binary"""

from argparse import ArgumentParser
from typing import Any, Optional

import darkgraylib.command_line
from darkgraylib.command_line import add_parser_argument
from graylint import help as hlp
from graylint.version import __version__


def make_argument_parser(require_src: bool) -> ArgumentParser:
    """Create the argument parser object

    :param require_src: ``True`` to require at least one path as a positional argument
                        on the command line. ``False`` to not require on.
    :param description: The descriptive text for the application to be shown in
                        ``--help`` output.

    """
    parser = darkgraylib.command_line.make_argument_parser(
        require_src,
        "Graylint",
        hlp.DESCRIPTION,
        "Read Graylint configuration from `PATH`. Note that linters run by Graylint"
        " won't read this configuration file.",
        __version__
    )

    def add_arg(help_text: Optional[str], *name_or_flags: str, **kwargs: Any) -> None:
        kwargs["help"] = help_text
        parser.add_argument(*name_or_flags, **kwargs)

    add_arg(hlp.LINT, "-L", "--lint", action="append", metavar="CMD", default=[])
    return parser


def add_lint_arg(parser: ArgumentParser) -> None:
    """Add the ``-L`` / ``--lint`` argument to the parser

    :parser: The parser to add the argument to

    """
    add_parser_argument(
        parser, hlp.LINT, "-L", "--lint", action="append", metavar="CMD", default=[]
    )

"""Command line parsing for the ``graylint`` binary"""

from argparse import ArgumentParser

import darkgraylib.command_line
from graylint import help as hlp
from graylint.version import __version__


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

import logging
import sys
from argparse import ArgumentError

from darkgraylib.command_line import parse_command_line
from darkgraylib.config import show_config_if_debug
from darkgraylib.git import RevisionRange
from darkgraylib.highlighting import should_use_color
from darkgraylib.log import setup_logging
from darkgraylib.main import resolve_paths

from graylint.command_line import make_argument_parser
from graylint.config import GraylintConfig
from graylint.linting import run_linters


logger = logging.getLogger(__name__)


def main_with_error_handling() -> int:
    """Entry point for console script"""
    try:
        return main()
    except ArgumentError as exc_info:
        if logger.root.level < logging.WARNING:
            raise
        sys.exit(str(exc_info))


def main():
    args, config, config_nondefault = parse_command_line(
        make_argument_parser, sys.argv[1:], "graylint", GraylintConfig
    )
    setup_logging(args.log_level)
    show_config_if_debug(config, config_nondefault, args.log_level)
    paths, root = resolve_paths(args.stdin_filename, args.src)
    revrange = RevisionRange.parse_with_common_ancestor(
        args.revision, root, args.stdin_filename is not None
    )
    linter_failures_on_modified_lines = run_linters(
        args.lint,
        root,
        # paths to lint are not limited to modified files or just Python files:
        {p.resolve().relative_to(root) for p in paths},
        revrange,
        use_color=should_use_color(config["color"]),
    )


if __name__ == "__main__":
    RETVAL = main_with_error_handling()
    sys.exit(RETVAL)

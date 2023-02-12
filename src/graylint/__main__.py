import logging
import sys
from argparse import ArgumentError
from typing import List

logger = logging.getLogger(__name__)


def main_with_error_handling() -> int:
    """Entry point for console script"""
    try:
        return main()
    except ArgumentError as exc_info:
        if logger.root.level < logging.WARNING:
            raise
        sys.exit(str(exc_info))


def main(argv: List[str] = None) -> int:
    ...


if __name__ == "__main__":
    RETVAL = main_with_error_handling()
    sys.exit(RETVAL)

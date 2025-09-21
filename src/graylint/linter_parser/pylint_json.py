import json
import logging
from collections import defaultdict
from pathlib import Path

from graylint.linter_parser.base import LinterParser
from graylint.linter_parser.message import (
    DISCARDED_LINE,
    LinterMessage,
    MessageLocation,
)

logger = logging.getLogger(__name__)


NEED_KEYS = {
    "path": str,
    "line": int,
    "column": int,
    "message": str,
    "message-id": str,
    "symbol": str,
}


class PylintJsonParserPlugin(LinterParser):
    name = "pylint-json"

    def parse(
        self, linter: str, linter_output: str, cwd: Path
    ) -> dict[MessageLocation, list[LinterMessage]]:
        """Parse the output of Pylint in JSON format

        :param linter_output: The complete output of the linter
        :return: A mapping of linter message locations to linter messages

        """
        messages: dict[MessageLocation, list[LinterMessage]] = defaultdict(list)
        try:
            entries = json.loads(linter_output)
        except json.JSONDecodeError as ex:
            logger.debug("Failed to parse %s output as JSON: %s", linter, ex)
            return messages
        if not isinstance(entries, list):
            logger.warning("Expected %s output to be a list", linter)
            return messages
        messages[DISCARDED_LINE].append(LinterMessage(linter, "pylint"))
        for entry in entries:
            if not isinstance(entry, dict):
                logger.warning("Expected entries in %s output to be objects", linter)
                continue
            if not (set(NEED_KEYS).issubset(entry)):
                logger.warning("Missing expected keys in an entry in %s output", linter)
                continue
            if not all(isinstance(entry[key], typ) for key, typ in NEED_KEYS.items()):
                logger.warning("Invalid types in an entry in %s output", linter)
                continue
            path = Path(entry["path"])
            location = MessageLocation(path, entry["line"], entry["column"])
            message_id = entry["message-id"]
            message_text = entry["message"]
            symbol = entry["symbol"]
            message = LinterMessage(linter, f"{message_id}: {message_text} ({symbol})")
            messages[location].append(message)
        return messages

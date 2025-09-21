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


NEED_KEYS = {"file": str, "severity": str, "message": str, "range": dict, "rule": str}
NEED_START_KEYS = {"line", "character"}


class PyrightJsonParserPlugin(LinterParser):
    name = "pyright-json"

    def parse(
        self, linter: str, linter_output: str, cwd: Path
    ) -> dict[MessageLocation, list[LinterMessage]]:
        """Parse the output of Pyright or Basedpyright in JSON format

        :param linter_output: The complete output of the linter
        :return: A mapping of linter message locations to linter messages

        """
        messages: dict[MessageLocation, list[LinterMessage]] = defaultdict(list)
        try:
            data = json.loads(linter_output)
        except json.JSONDecodeError as ex:
            logger.debug("Failed to parse %s output as JSON: %s", linter, ex)
            return messages
        if not isinstance(data, dict):
            logger.warning("Expected %s output to be a JSON object", linter)
            return messages
        if "generalDiagnostics" not in data:
            logger.info("No 'generalDiagnostics' in %s output", linter)
            return messages
        if not isinstance(data["generalDiagnostics"], list):
            logger.warning(
                "Expected 'generalDiagnostics' in %s output to be a list", linter
            )
            return messages
        messages[DISCARDED_LINE].append(LinterMessage(linter, "generalDiagnostics"))
        for diag in data["generalDiagnostics"]:
            if not isinstance(diag, dict):
                logger.warning(
                    "Entries in 'generalDiagnostics' in %s output must be objects",
                    linter,
                )
                continue
            if not (
                set(NEED_KEYS).issubset(diag)
                and "start" in diag["range"]
                and NEED_START_KEYS.issubset(diag["range"]["start"])
            ):
                logger.warning(
                    "Missing keys in a 'generalDiagnostics' entry in %s output",
                    linter,
                )
                continue
            start = diag["range"]["start"]
            if not (
                all(isinstance(diag[key], typ) for key, typ in NEED_KEYS.items())
                and all(isinstance(start[key], int) for key in NEED_START_KEYS)
            ):
                logger.warning(
                    "Invalid types in a 'generalDiagnostics' entry in %s output",
                    linter,
                )
                continue
            path = Path(diag["file"])
            location = MessageLocation(path, start["line"], start["character"])
            severity = diag["severity"]
            message_text = diag["message"]
            rule = diag["rule"]
            message = LinterMessage(linter, f"{severity}: {message_text} ({rule})")
            messages[location].append(message)
        return messages

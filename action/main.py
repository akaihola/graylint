"""Graylint GitHub action implementation"""

from __future__ import annotations

import os
import re
import shlex
import sys
from pathlib import Path
from subprocess import PIPE, STDOUT, run  # nosec
from typing import TYPE_CHECKING

from pip_requirements_parser import parse_reqparts_from_string

if TYPE_CHECKING:
    from pip_requirements_parser import RequirementParts


LINTER_WHITELIST = {"flake8", "pylint", "mypy", "ruff"}
ACTION_PATH = Path(os.environ["GITHUB_ACTION_PATH"])
ENV_PATH = ACTION_PATH / ".graylint-env"
ENV_BIN = ENV_PATH / ("Scripts" if sys.platform == "win32" else "bin")
OPTIONS = os.getenv("INPUT_OPTIONS", default="")
SRC = os.getenv("INPUT_SRC", default="")
VERSION = os.getenv("INPUT_VERSION", default="")
LINT = os.getenv("INPUT_LINT", default="")
WITH = os.getenv("INPUT_WITH", default="")
REVISION = os.getenv("INPUT_REVISION") or os.getenv("INPUT_COMMIT_RANGE") or "HEAD^"

run([sys.executable, "-m", "venv", str(ENV_PATH)], check=True)  # nosec

req = ["graylint[color]"]
if VERSION:
    if VERSION.startswith("@"):
        req[0] = f"git+https://github.com/akaihola/graylint{VERSION}#egg={req[0]}"
    elif VERSION.startswith(("~", "=", "<", ">")):
        req[0] += VERSION
    else:
        req[0] += f"=={VERSION}"
linter_options = []


def split_requirements_string(requirements_string: str) -> list[RequirementParts]:
    """Split requirements string into parts."""
    return [
        parse_reqparts_from_string(part.strip()).requirement
        for part in re.split(r"\s*[,\s]\s*(?=[a-zA-Z_])", requirements_string)
        if part.strip()
    ]


for linter_requirement in split_requirements_string(LINT):
    linter = linter_requirement.name
    if linter not in LINTER_WHITELIST:
        raise RuntimeError(
            f"{linter!r} is not supported as a linter by the GitHub Action"
        )
    req.append(str(linter_requirement))
    linter_options.extend(["--lint", linter])
req.extend(str(r) for r in split_requirements_string(WITH))

pip_proc = run(  # nosec
    [str(ENV_BIN / "python"), "-m", "pip", "install"] + req,
    check=False,
    stdout=PIPE,
    stderr=STDOUT,
    encoding="utf-8",
)
print(pip_proc.stdout, end="")
if pip_proc.returncode:
    print(f"::error::Failed to install {' '.join(req)}.", flush=True)
    sys.exit(pip_proc.returncode)


base_cmd = [str(ENV_BIN / "graylint")]
proc = run(  # nosec
    [
        *base_cmd,
        *shlex.split(OPTIONS),
        *linter_options,
        "--revision",
        REVISION,
        *shlex.split(SRC),
    ],
    check=False,
    stdout=PIPE,
    stderr=STDOUT,
    env={**os.environ, "PATH": f"{ENV_BIN}:{os.environ['PATH']}"},
    encoding="utf-8",
)
print(proc.stdout, end="")

sys.exit(proc.returncode)

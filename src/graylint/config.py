"""Load and save configuration in TOML format"""

from __future__ import annotations

from typing import TYPE_CHECKING

from darkgraylib.config import BaseConfig

if TYPE_CHECKING:
    from graylint.command_line import OutputSpec


class GraylintConfig(BaseConfig):
    """Dictionary representing ``[tool.graylint]`` from ``pyproject.toml``"""

    lint: list[str]
    output_format: dict[str, OutputSpec]

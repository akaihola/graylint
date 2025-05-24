"""Load and save configuration in TOML format"""

from __future__ import annotations

from darkgraylib.config import BaseConfig


class GraylintConfig(BaseConfig):
    """Dictionary representing ``[tool.graylint]`` from ``pyproject.toml``"""

    lint: list[str]
    output_format: dict[str, str]

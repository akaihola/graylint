"""Load and save configuration in TOML format"""

from typing import List
from darkgraylib.config import BaseConfig


class GraylintConfig(BaseConfig):
    """Dictionary representing ``[tool.graylint]`` from ``pyproject.toml``"""

    lint: List[str]

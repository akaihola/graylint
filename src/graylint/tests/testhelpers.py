"""Platform-specific test skipping."""

import pytest

from darkgraylib.utils import WINDOWS

SKIP_ON_WINDOWS = [pytest.mark.skip] if WINDOWS else []
SKIP_ON_UNIX = [] if WINDOWS else [pytest.mark.skip]

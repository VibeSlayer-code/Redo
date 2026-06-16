import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def disable_update_check(monkeypatch):
    monkeypatch.setenv("REDO_DISABLE_UPDATE_CHECK", "1")

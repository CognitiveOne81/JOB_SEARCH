from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / 'test_jobs.db'
    monkeypatch.setenv('JOB_SEARCH_DB_PATH', str(db_path))
    yield
    if db_path.exists():
        os.remove(db_path)

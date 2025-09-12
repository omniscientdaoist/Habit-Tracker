# tests/conftest.py
import pytest

from habit_tracker.habit import HabitTracker


@pytest.fixture()
def tracker(tmp_path):
    db_path = tmp_path / "habits.db"
    ht = HabitTracker(str(db_path))
    return ht

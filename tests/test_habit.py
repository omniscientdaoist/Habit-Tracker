import pytest
from habit_tracker.habit import add_habit, mark_habit_done, delete_habit, edit_habit, get_dashboard


def test_add_habit():
    h = add_habit("pray")
    assert h["name"] == "pray"
    assert h["streak"] == 0
    assert h["last_done"] is None


def test_mark_habit_done_first_time():
    habits = [add_habit("pray")]
    status = mark_habit_done(habits, 1)  # returns status string
    assert status in ("incremented", "reset_to_1")  # depending on your logic branch
    assert habits[0]["streak"] == 1
    assert habits[0]["last_done"] is not None


def test_delete_habit():
    habits = [add_habit("pray"), add_habit("read")]
    status, removed = delete_habit(habits, "1")  # tuple per your current impl
    assert status == "deleted"
    assert removed["name"] == "pray"
    assert len(habits) == 1
    assert habits[0]["name"] == "read"


def test_edit_habit():
    habits = [add_habit("kill"), add_habit("bot")]
    status = edit_habit(habits, 1, "Kill", 2, "20-08-2025")
    assert status == "edited"


def test_get_dashboard():
    habits = [add_habit("kill"), add_habit("bot")]
    status = get_dashboard(habits)
    # Check the order of names
    assert [h["name"] for h in status] == ["kill", "bot"]

    # Check that both are "new" habits
    for h in status:
        assert h["streak"] == 0
        assert h["days_since"] is None
        assert h["stale"] is False

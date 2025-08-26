import pytest
from habit import add_habit, mark_habit_done, delete_habit

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

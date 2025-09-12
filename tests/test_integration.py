def test_add_list_delete(tracker):
    assert tracker.add("pray") == "added"
    assert tracker.add("read") == "added"

    items = tracker.list()
    assert [h["name"] for h in items] == ["pray", "read"]

    status, removed = tracker.delete(1)    # 1-based
    assert status == "deleted"
    assert removed["name"] == "pray"
    assert [h["name"] for h in tracker.list()] == ["read"]

def test_done_streaks(tracker, monkeypatch):
    # Fix “today” so test is deterministic
    from datetime import date, timedelta

    fixed_today = date(2025, 9, 12)
    def fake_today(): return fixed_today
    monkeypatch.setattr("habit_tracker.habit._today", fake_today)

    tracker.add("gym")

    # mark yesterday then today → incremented
    yday = (fixed_today - timedelta(days=1)).strftime("%d-%m-%Y")
    assert tracker.complete_on(1, yday) == "added"
    assert tracker.done(1) == "incremented"

    dash = tracker.dashboard()
    row = next(r for r in dash if r["name"] == "gym")
    assert row["streak"] == 2
    assert row["days_since"] == 0

def test_stats_basic(tracker, monkeypatch):
    from datetime import date, timedelta
    fixed_today = date(2025, 9, 12)
    monkeypatch.setattr("habit_tracker.habit._today", lambda: fixed_today)

    tracker.add("code")
    tracker.add("read")

    d1 = (fixed_today - timedelta(days=2)).strftime("%d-%m-%Y")
    d2 = (fixed_today - timedelta(days=1)).strftime("%d-%m-%Y")
    d3 = fixed_today.strftime("%d-%m-%Y")

    tracker.complete_on(1, d1)
    tracker.complete_on(1, d2)
    tracker.complete_on(2, d2)
    tracker.complete_on(1, d3)

    rep = tracker.stats(days=3)
    assert rep["per_day"][d2] == 2      # two completions on d2
    assert rep["per_habit"]["code"] == 3
    assert rep["current_streak"]["code"] == 3

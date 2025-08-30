from __future__ import annotations

import builtins
import json
from datetime import datetime, timedelta

DateFmt = "%d-%m-%Y"


def _today():
    return datetime.today().date()


def _parse_date(s: str) -> datetime.date | None:
    try:
        return datetime.strptime(s, DateFmt).date()
    except Exception:
        return None


class HabitTracker:
    """
    Minimal class-based Habit Tracker.
    - Holds habits in memory (self.habits).
    - Persists to a JSON file (self.path).
    - Methods return status strings so the CLI can decide what to print.

    Habit shape (dict):
        {
            "name": str,
            "streak": int,
            "last_done": Optional[str],  # "DD-MM-YYYY" or None
        }
    """

    def __init__(self, path: str = "habits.json"):
        self.path = path
        self.habits: list[dict] = []
        self.load()

    def load(self) -> None:
        """Load habits from self.path into self.habits."""
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
                self.habits = data if isinstance(data, list) else []
        except FileNotFoundError:
            self.habits = []
        except json.JSONDecodeError:
            self.habits = []

    def save(self) -> None:
        """Save self.habits into self.path."""
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.habits, f, indent=4)

    def add(self, name: str) -> str:
        """Add a new habit. Returns 'added' or 'empty_name'."""
        name = (name or "").strip()
        if not name:
            return "empty_name"
        self.habits.append({"name": name, "streak": 0, "last_done": None})
        self.save()
        return "added"

    def delete(self, index_1based: int) -> tuple[str, dict | None]:
        """
        Delete a habit by 1-based index.
        Returns ('deleted', removed_dict) or ('bad_index', None).
        """
        idx = index_1based - 1
        if idx < 0 or idx >= len(self.habits):
            return "bad_index", None
        removed = self.habits.pop(idx)
        self.save()
        return "deleted", removed

    def edit(self, index_1based: int, name: str = "", streak: int = "", date: str = "") -> str:
        """
        Edit fields. Returns: 'edited', 'nothing', 'invalid_streak', 'invalid_date', 'bad_index'
        """
        idx = index_1based - 1
        if idx < 0 or idx >= len(self.habits):
            return "bad_index"

        habit = self.habits[idx]
        changed = False

        if name:
            new_name = name.strip()
            if new_name != habit.get("name", ""):
                habit["name"] = new_name
                changed = True

        if streak != "":
            try:
                s = int(streak)
            except ValueError:
                return "invalid_streak"
            if s < 0:
                return "invalid_streak"
            if s != habit.get("streak", 0):
                habit["streak"] = s
                changed = True

        if date:
            dt = _parse_date(date.strip())
            if not dt:
                return "invalid_date"
            new_date = dt.strftime(DateFmt)
            if new_date != habit.get("last_done", None):
                habit["last_done"] = new_date
                changed = True

        if changed:
            self.save()
            return "edited"

        return "nothing"

    def done(self, index_1based: int) -> str:
        """
        Mark a habit as done today.
        Returns: 'already', 'incremented', 'reset_to_1', 'bad_index'
        """

        idx = index_1based - 1

        if idx < 0 or idx >= len(self.habits):
            return "bad_index"

        habit = self.habits[idx]
        today = _today()
        yesterday = today - timedelta(days=1)

        last = habit.get("last_done")
        last_date = _parse_date(last) if last else None

        if last_date == today:
            return "already"

        elif last_date == yesterday:
            habit["streak"] = habit.get("streak", 0) + 1
            habit["last_done"] = today.strftime(DateFmt)
            self.save()
            return "incremented"

        else:
            habit["streak"] = 1
            habit["last_done"] = today.strftime(DateFmt)
            self.save()
            return "reset_to_1"

    def list(self) -> builtins.list[dict]:
        """Return a copy of habits (so callers don’t mutate internal list by accident)."""
        return list(self.habits)

    def days_since(self, date_str: str | None) -> int | None:
        if not date_str:
            return None
        d = _parse_date(date_str)
        if not d:
            return None
        return (_today() - d).days

    def dashboard(self) -> builtins.list[dict]:
        """
        Compute a dashboard list of dicts:
            { name, streak, days_since, stale }
        Sort order: stale first, then by days_since desc, then streak desc.
        """
        rows = []
        for h in self.habits:
            ds = self.days_since(h.get("last_done"))
            stale = (ds is not None) and (ds >= 2)
            rows.append(
                {
                    "name": h.get("name", "Untitled"),
                    "streak": h.get("streak", 0),
                    "days_since": ds,
                    "stale": stale,
                }
            )

        def sort_key(row):
            # stale first (True sorts before False if we invert), then larger days_since, then larger streak
            days = row["days_since"] if row["days_since"] is not None else -1
            return (not row["stale"], -days, -row["streak"])

        return sorted(rows, key=sort_key)

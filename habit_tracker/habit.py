# habit_tracker/habit_tracker.py
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from habit_tracker.repo import HabitRepo  # <-- use the repo

DateFmt = "%d-%m-%Y"


def _today():
    return datetime.today().date()


def _today_str() -> str:
    return _today().strftime(DateFmt)


def _yesterday_str() -> str:
    return (_today() - timedelta(days=1)).strftime(DateFmt)


def _parse_date(s: str) -> datetime.date | None:
    try:
        return datetime.strptime(s, DateFmt).date()
    except Exception:
        return None


class HabitTracker:
    """
    Class now backed by SQLite via HabitRepo.
    Public methods/return statuses unchanged.
    """

    def __init__(self, path: str = "habits.db"):
        # 'path' is the DB file now (e.g., habits.db)
        self.repo = HabitRepo(path)

    # ---------- Queries / reads ----------

    def list(self) -> list[dict]:
        """Return all habits as a list of dicts (fresh from DB)."""
        return self.repo.fetch_all()

    def dashboard(self) -> list[dict]:
        rows = []
        today_s = _today_str()
        yday_s = _yesterday_str()
        for h in self.list():
            # pull completion dates for this habit and put into a set of 'DD-MM-YYYY'
            comps = {row["done_on"] for row in self.repo.fetch_completions(h["id"])}
            ds = self._days_since_from_dates(comps)
            stale = (ds is not None) and (ds >= 2)
            streak = self._compute_streak_from_completions(comps, today_s, yday_s)
            rows.append(
                {
                    "name": h.get("name", "Untitled"),
                    "streak": streak,
                    "days_since": ds,
                    "stale": stale,
                }
            )

        def sort_key(row):
            # stale first, then by days_since desc, then streak desc
            days = row["days_since"] if row["days_since"] is not None else -1
            return (not row["stale"], -days, -row["streak"])

        return sorted(rows, key=sort_key)

    # ---------- Commands / writes ----------

    def add(self, name: str) -> str:
        name = (name or "").strip()
        if not name:
            return "empty_name"
        self.repo.insert(name=name, streak=0, last_done=None)
        return "added"

    def delete(self, index_1based: int) -> tuple[str, dict | None]:
        habits = self.list()
        idx = index_1based - 1
        if idx < 0 or idx >= len(habits):
            return "bad_index", None
        removed = habits[idx]
        self.repo.delete(removed["id"])
        return "deleted", removed

    def edit(self, index_1based: int, name: str = "", streak: str = "", date: str = "") -> str:
        habits = self.list()
        idx = index_1based - 1
        if idx < 0 or idx >= len(habits):
            return "bad_index"
        h = habits[idx]

        changed = False
        new_name = None
        new_streak = None
        new_last_done = None

        if name:
            candidate = name.strip()
            if candidate and candidate != h["name"]:
                new_name = candidate
                changed = True

        if streak != "":
            try:
                s = int(streak)
            except ValueError:
                return "invalid_streak"
            if s < 0:
                return "invalid_streak"
            if s != h["streak"]:
                new_streak = s
                changed = True

        if date:
            dt = _parse_date(date.strip())
            if not dt:
                return "invalid_date"
            candidate = dt.strftime(DateFmt)
            if candidate != (h.get("last_done") or ""):
                new_last_done = candidate
                changed = True

        if not changed:
            return "nothing"

        self.repo.update(h["id"], name=new_name, streak=new_streak, last_done=new_last_done)
        return "edited"

    def done(self, index_1based: int) -> str:
        habits = self.list()
        idx = index_1based - 1
        if idx < 0 or idx >= len(habits):
            return "bad_index"

        h = habits[idx]
        today_str = _today_str()
        yesterday_str = _yesterday_str()

        # already completed today?
        if self.repo.has_completion_on(h["id"], today_str):
            return "already"

        # write today's completion (idempotent with INSERT OR IGNORE in repo)
        self.repo.add_completion(h["id"], today_str)

        # if we also have a completion yesterday → streak increments
        if self.repo.has_completion_on(h["id"], yesterday_str):
            return "incremented"
        else:
            return "reset_to_1"

    def _days_since_from_dates(self, dates: set[str]) -> int | None:
        if not dates:
            return None
        last = max(datetime.strptime(d, DateFmt).date() for d in dates)
        return (_today() - last).days

    def _compute_streak_from_completions(
        self, dates: set[str], today_str: str, yesterday_str: str
    ) -> int:
        # start at today if present, else yesterday if present, else 0
        if today_str in dates:
            start = today_str
        elif yesterday_str in dates:
            start = yesterday_str
        else:
            return 0

        def prev(dstr: str) -> str:
            d = datetime.strptime(dstr, DateFmt).date()
            return (d - timedelta(days=1)).strftime(DateFmt)

        streak = 0
        cur = start
        while cur in dates:
            streak += 1
            cur = prev(cur)
        return streak

    def _longest_streak_from_dates(self, dates: set[str]) -> int:
        """
        Longest run of consecutive days inside `dates` (strings DD-MM-YYYY).
        O(n log n) via set lookups + local backtracking.
        """
        if not dates:
            return 0

        def prev(dstr: str) -> str:
            d = datetime.strptime(dstr, DateFmt).date()
            return (d - timedelta(days=1)).strftime(DateFmt)

        # Longest chain by only starting from “heads” (no previous day in set)
        dates_set = set(dates)
        longest = 0
        for d in dates_set:
            if prev(d) not in dates_set:  # start of a run
                length = 1
                cur = d
                while True:
                    nxt = datetime.strptime(cur, DateFmt).date() + timedelta(days=1)
                    nxt_s = nxt.strftime(DateFmt)
                    if nxt_s in dates_set:
                        length += 1
                        cur = nxt_s
                    else:
                        break
                if length > longest:
                    longest = length
        return longest

    def unmark(self, index: int) -> str:
        habits = self.list()
        idx = index - 1
        if idx < 0 or idx >= len(habits):
            return "bad_index"

        h = habits[idx]
        today_str = _today_str()

        if self.repo.delete_completion(h["id"], today_str):
            return "removed_today"

        return "nothing_to_remove"

    def _label_relative(self, date_str: str) -> str:
        """Return 'today' / 'yesterday' / 'N days ago' (or 'in N days' if future)."""
        d = datetime.strptime(date_str, DateFmt).date()
        delta = (_today() - d).days
        if delta == 0:
            return "today"
        if delta == 1:
            return "yesterday"
        if delta > 1:
            return f"{delta} days ago"
        # future date guard (shouldn't normally happen)
        return f"in {-delta} days"

    def history(
        self, index: int, limit: int | None = None, newest_first: bool = True
    ) -> list[dict] | str:
        """
        Return a list of completions with relative labels for a habit:
        [{ "done_on": "21-08-2025", "label": "yesterday" }, ...]
        newest_first: reverse chronological order if True.
        limit: cap results (e.g., last 10).
        """
        habits = self.list()
        idx = index - 1
        if idx < 0 or idx >= len(habits):
            return "bad_index"

        h = habits[idx]
        rows = self.repo.fetch_completions(h["id"])  # [{ "done_on": "..."}, ...] ASC by date

        if not rows:
            return []

        if newest_first:
            rows = list(reversed(rows))

        if limit is not None:
            rows = rows[:limit]

        # attach relative label
        out = []
        for r in rows:
            d = r["done_on"]
            out.append({"done_on": d, "label": self._label_relative(d)})
        return out

    def complete_on(self, index: int, date_str: str) -> str:

        habits = self.list()
        idx = index - 1
        if idx < 0 or idx >= len(habits):
            return "bad_index"

        try:
            date = datetime.strptime(date_str, DateFmt).date()
        except ValueError:
            return "invalid_date"

        delta = (_today() - date).days
        if delta < 0:
            return "future_date"

        habit = habits[idx]
        habit_id = habit["id"]
        if self.repo.has_completion_on(habit_id, date_str):
            return "already"

        self.repo.add_completion(habit_id, date_str)
        return "added"

    def uncomplete_on(self, index: int, date_str: str) -> str:
        """
        Remove a completion for a given habit (1-based index) on a specific date (DD-MM-YYYY).

        Returns one of:
        - 'bad_index'          : index out of range
        - 'invalid_date'       : date_str not parseable with DateFmt
        - 'removed'            : deletion succeeded (a row was removed)
        - 'nothing_to_remove'  : no completion existed for that day
        """
        habits = self.list()
        idx = index - 1
        if idx < 0 or idx >= len(habits):
            return "bad_index"

        # Validate the format (and guard typos)
        try:
            _ = datetime.strptime(date_str, DateFmt).date()
        except ValueError:
            return "invalid_date"

        habit_id = habits[idx]["id"]

        # One-step delete; rowcount tells us if anything was removed
        removed = self.repo.delete_completion(habit_id, date_str)
        return "removed" if removed else "nothing_to_remove"

    def stats(self, days: int = 30) -> dict:
        """
        Aggregate analytics for the last `days` ending at today (inclusive).
        Returns dict:
        {
            "window": {"start": "DD-MM-YYYY", "end": "DD-MM-YYYY"},
            "per_day": { "DD-MM-YYYY": int, ... },
            "per_habit": { "Habit Name": int, ... },
            "current_streak": { "Habit Name": int, ... },
            "longest_streak": { "Habit Name": int, ... }
        }
        """
        end_d = _today()
        start_d = end_d - timedelta(days=days - 1)
        start_s = start_d.strftime(DateFmt)
        end_s = end_d.strftime(DateFmt)

        # map habit_id -> name
        habits = self.list()
        id_to_name = {h["id"]: h["name"] for h in habits}

        rows = self.repo.fetch_completions_between(start_s, end_s)

        # per_day totals
        per_day = defaultdict(int)
        # per_habit totals (within window)
        per_habit = defaultdict(int)
        # group completions per habit to compute streaks
        by_habit_dates = defaultdict(set)

        for r in rows:
            hid = r["habit_id"]
            d = r["done_on"]
            per_day[d] += 1
            per_habit[id_to_name.get(hid, f"#{hid}")] += 1
            by_habit_dates[hid].add(d)

        # compute current + longest streak per habit from date sets
        current_streak = {}
        longest_streak = {}

        today_s = end_s
        yday_s = (end_d - timedelta(days=1)).strftime(DateFmt)

        for hid, name in id_to_name.items():
            dates = by_habit_dates.get(hid, set())
            current_streak[name] = self._compute_streak_from_completions(dates, today_s, yday_s)
            longest_streak[name] = self._longest_streak_from_dates(dates)

        return {
            "window": {"start": start_s, "end": end_s},
            "per_day": dict(per_day),
            "per_habit": dict(per_habit),
            "current_streak": current_streak,
            "longest_streak": longest_streak,
        }

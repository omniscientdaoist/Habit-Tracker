import argparse
import logging
import os

from habit_tracker.habit import DateFmt, HabitTracker


# ---------- simple presentation helpers ----------
def format_habit_line(index: int, habit: dict) -> str:
    name = habit.get("name", "Untitled")
    streak = habit.get("streak", 0)
    last_done = habit.get("last_done") or "Never"
    return f"{index}. {name} — Streak {streak}, Last done {last_done}"


def format_dashboard_line(row: dict) -> str:
    name = row["name"]
    streak = row["streak"]
    ds = row["days_since"]

    if ds is None:
        badge = "🆕 NEW  "
        when = "never done"
    elif ds == 0:
        badge = "✅ TODAY"
        when = "done today"
    elif ds >= 2:
        badge = "🔥 STALE"
        when = f"last done {ds} day(s) ago"
    else:  # ds == 1
        badge = "⌛ ACTIVE"
        when = "last done yesterday"

    return f"{badge} | {name} — streak {streak} | {when}"


# ---------- command handlers wired to the class ----------
def cmd_add(args):
    ht = HabitTracker(args.data)
    status = ht.add(args.name)
    if status == "added":
        print(f"✅ Habit '{args.name}' added.")
    elif status == "empty_name":
        print("❌ Cannot add an empty habit.")


def cmd_list(args):
    ht = HabitTracker(args.data)
    habits = ht.list()
    if not habits:
        print("No habits yet.")
        return
    for i, h in enumerate(habits, 1):
        print(format_habit_line(i, h))


def cmd_done(args):
    ht = HabitTracker(args.data)
    status = ht.done(args.index)  # 1-based index
    if status == "already":
        print("ℹ️ Already marked today.")
    elif status == "incremented":
        print("✅ Marked. Streak incremented.")
    elif status == "reset_to_1":
        print("✅ Marked. Streak reset to 1.")
    elif status == "bad_index":
        print("❌ Invalid number.")
    else:
        print("❌ Unknown error.")

def cmd_unmark(args):
    ht = HabitTracker(args.data)
    status = ht.unmark(args.index)  # 1-based index
    if status == "removed_today":
        print("✅ Habit marked as undone.")
    elif status == "nothing_to_remove":
        print("ℹ️ Habit not marked as done.")
    elif status == "bad_index":
        print("❌ Invalid number.")
    else:
        print("❌ Unknown error.")

def cmd_delete(args):
    ht = HabitTracker(args.data)
    status, removed = ht.delete(args.index)  # 1-based index
    if status == "deleted":
        name = removed.get("name", "Unknown") if removed else "Unknown"
        print(f"🗑️ Deleted: {name}.")
    elif status == "bad_index":
        print("❌ Invalid number.")
    else:
        print("❌ Unknown error.")


def cmd_edit(args):
    """
    HabitTracker.edit expects a 1-based index (same as CLI).
    name/streak/date are optional; pass "" for untouched fields.
    """
    ht = HabitTracker(args.data)
    status = ht.edit(
        args.index,
        name=args.name or "",
        streak=args.streak or "",
        date=args.date or "",
    )
    if status == "edited":
        print("✏️ Edited.")
    elif status == "nothing":
        print("ℹ️ No changes made.")
    elif status == "invalid_streak":
        print("❌ Invalid streak. Use a non-negative integer.")
    elif status == "invalid_date":
        print(f"❌ Invalid date. Use {DateFmt}.")
    elif status == "bad_index":
        print("❌ Invalid number.")
    else:
        print("❌ Unknown error.")


def cmd_dashboard(args):
    ht = HabitTracker(args.data)
    rows = ht.dashboard()
    if not rows:
        print("No habits yet.")
        return
    for row in rows:
        print(format_dashboard_line(row))

def cmd_history(args):
    ht = HabitTracker(args.data)  # or HabitTracker() if you default the path
    rows = ht.history(args.index, args.limit, not args.oldest)  # 1-based index

    if rows == "bad_index":
        print("❌ Invalid number.")
        return

    if not rows:
        print("No 📜 history for this habit.")
        return

    # status == "ok"
    print("📜 History:")
    for r in rows:
        # e.g. "03-09-2025  (today)" or "01-09-2025  (2d ago)"
        print(f"- {r['done_on']}  ({r['label']})")

def cmd_add_date(args):
    ht = HabitTracker(args.data)  # if your tracker takes a db path; else HabitTracker()
    status = ht.complete_on(args.index, args.date)

    if status == "bad_index":
        print("❌ Invalid number.")
    elif status == "invalid_date":
        print("❌ Invalid date. Use DD-MM-YYYY.")
    elif status == "future_date":
        print("❌ Date is in the future.")
    elif status == "already":
        print("ℹ️ That date is already recorded.")
    elif status == "added":
        print("✅ Date added.")
    else:
        print("❌ Unknown error.")


def cmd_remove_date(args):
    ht = HabitTracker(args.data)  # if your tracker takes a db path; else HabitTracker()
    status = ht.uncomplete_on(args.index, args.date)

    if status == "bad_index":
        print("❌ Invalid number.")
    elif status == "invalid_date":
        print("❌ Invalid date. Use DD-MM-YYYY.")
    elif status == "removed":
        print("✅ Date removed.")
    elif status == "nothing_to_remove":
        print("No date found.")
    else:
        print("❌ Unknown error.")

def cmd_stats(args):
    ht = HabitTracker(args.data)
    report = ht.stats(days=args.days)

    w = report["window"]
    print(f"📊 Stats for {w['start']} → {w['end']}\n")

    print("Per-day totals:")
    if report["per_day"]:
        for day, cnt in sorted(report["per_day"].items()):
            print(f"  {day}: {cnt}")
    else:
        print("  (no completions)")

    print("\nPer-habit totals:")
    if report["per_habit"]:
        for name, cnt in sorted(report["per_habit"].items(), key=lambda x: (-x[1], x[0])):
            print(f"  {name}: {cnt}")
    else:
        print("  (no completions)")

    print("\nCurrent streaks:")
    for name, s in sorted(report["current_streak"].items(), key=lambda x: (-x[1], x[0])):
        print(f"  {name}: {s}")

    print("\nLongest streaks:")
    for name, s in sorted(report["longest_streak"].items(), key=lambda x: (-x[1], x[0])):
        print(f"  {name}: {s}")

    if args.chart:
        print("\nPer-day chart (ASCII):")
        print(render_bar_chart(report["per_day"], width=40))

def render_bar_chart(per_day: dict[str, int], width: int = 40) -> str:
    """
    Render a left-to-right bar chart.
    Example line:  03-09-2025 | ██████ 6
    """
    if not per_day:
        return "(no data)"

    lines = []
    max_val = max(per_day.values())
    if max_val <= 0:
        max_val = 1

    for day, val in sorted(per_day.items()):
        bar_len = int((val / max_val) * width)
        bar = "█" * bar_len
        lines.append(f"{day} | {bar} {val}")
    return "\n".join(lines)


# ---------- argparse + logging ----------
def build_parser():
    p = argparse.ArgumentParser(prog="habits", description="Habit Tracker (subcommands)")
    group = p.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")
    group.add_argument("-q", "--quiet", action="store_true", help="Only errors")

    default_path = os.getenv("HABITS_PATH", "habits.db")
    p.add_argument("--data", default=default_path, help="Path to data file")


    sub = p.add_subparsers(dest="command", required=True)

    sp_add = sub.add_parser("add", help="Add a new habit")
    sp_add.add_argument("name", help="Habit name (quoted if contains spaces)")
    sp_add.set_defaults(func=cmd_add)

    sp_list = sub.add_parser("list", help="List all habits")
    sp_list.set_defaults(func=cmd_list)

    sp_done = sub.add_parser("done", help="Mark habit as done (by 1-based index)")
    sp_done.add_argument("index", type=int, help="Habit number (1-based)")
    sp_done.set_defaults(func=cmd_done)

    sp_unmark = sub.add_parser("unmark", help="Mark habit as undone (by 1-based index)")
    sp_unmark.add_argument("index", type=int, help="Habit number (1-based)")
    sp_unmark.set_defaults(func=cmd_unmark)

    sp_delete = sub.add_parser("delete", help="Delete habit (by 1-based index)")
    sp_delete.add_argument("index", type=int, help="Habit number (1-based)")
    sp_delete.set_defaults(func=cmd_delete)

    sp_edit = sub.add_parser("edit", help="Edit habit fields")
    sp_edit.add_argument("index", type=int, help="Habit number (1-based)")
    sp_edit.add_argument("--name", help="New name")
    sp_edit.add_argument("--streak", help="New streak (non-negative int)")
    sp_edit.add_argument("--date", help=f"New last-done date ({DateFmt})")
    sp_edit.set_defaults(func=cmd_edit)

    sp_dash = sub.add_parser("dashboard", help="Show computed dashboard")
    sp_dash.set_defaults(func=cmd_dashboard)

    sp_hist = sub.add_parser("history", help="Show completion history (relative labels)")
    sp_hist.add_argument("index", type=int, help="Habit number (1-based)")
    sp_hist.add_argument("--limit", type=int, help="Limit on history")
    sp_hist.add_argument("--oldest", action="store_true", 
                         help="Show oldest first instead of newest first")
    sp_hist.set_defaults(func=cmd_history)

    sp_add_date = sub.add_parser("add-date", help="Add new date to a habit.")
    sp_add_date.add_argument("index", type=int, help="Habit number")
    sp_add_date.add_argument("date", help="New date for the habit.")
    sp_add_date.set_defaults(func=cmd_add_date)

    sp_rmv_date = sub.add_parser("rmv-date", help="Delete a date from a habit.")
    sp_rmv_date.add_argument("index", type=int, help="Habit number")
    sp_rmv_date.add_argument("date", help="Date to remove from the habit.")
    sp_rmv_date.set_defaults(func=cmd_remove_date)

    sp_stats = sub.add_parser("stats", help="Show analytics for last N days")
    sp_stats.add_argument("--days", type=int, default=30, help="Window size (default 30)")
    sp_stats.add_argument("--chart", action="store_true", 
                          help="Show ASCII chart of per-day totals")
    sp_stats.set_defaults(func=cmd_stats)

    return p


def configure_logging(verbosity: int, quiet: bool):
    if quiet:
        level = logging.ERROR
    else:
        level = logging.WARNING if verbosity == 0 else (
            logging.INFO if verbosity == 1 else logging.DEBUG
            )
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main():
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.verbose, args.quiet)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

import argparse
import logging

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
    ht = HabitTracker()
    status = ht.add(args.name)
    if status == "added":
        print(f"✅ Habit '{args.name}' added.")
    elif status == "empty_name":
        print("❌ Cannot add an empty habit.")


def cmd_list(args):
    ht = HabitTracker()
    habits = ht.list()
    if not habits:
        print("No habits yet.")
        return
    for i, h in enumerate(habits, 1):
        print(format_habit_line(i, h))


def cmd_done(args):
    ht = HabitTracker()
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


def cmd_delete(args):
    ht = HabitTracker()
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
    ht = HabitTracker()
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
    ht = HabitTracker()
    rows = ht.dashboard()
    if not rows:
        print("No habits yet.")
        return
    for row in rows:
        print(format_dashboard_line(row))


# ---------- argparse + logging ----------
def build_parser():
    p = argparse.ArgumentParser(prog="habits", description="Habit Tracker (subcommands)")
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v for INFO, -vv for DEBUG)",
    )
    p.add_argument("-q", "--quiet", action="store_true", help="Only show essential output")

    sub = p.add_subparsers(dest="command", required=True)

    sp_add = sub.add_parser("add", help="Add a new habit")
    sp_add.add_argument("name", help="Habit name (quoted if contains spaces)")
    sp_add.set_defaults(func=cmd_add)

    sp_list = sub.add_parser("list", help="List all habits")
    sp_list.set_defaults(func=cmd_list)

    sp_done = sub.add_parser("done", help="Mark habit as done (by 1-based index)")
    sp_done.add_argument("index", type=int, help="Habit number (1-based)")
    sp_done.set_defaults(func=cmd_done)

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

    return p


def configure_logging(verbosity: int):
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main():
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.verbose)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

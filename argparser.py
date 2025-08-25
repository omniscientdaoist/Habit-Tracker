import argparse
from save import load_habits, save_habits
from habit import (
    add_habit,
    mark_habit_done,
    get_dashboard,
    format_dashboard_line,
    format_habit_line,
    edit_habit,       # your edited version that returns status codes
    delete_habit      # returns: 'deleted' | 'bad_index' | 'invalid_input'
)

def cmd_add(args):
    habits = load_habits()
    habits.append(add_habit(args.name))
    save_habits(habits)
    print(f"✅ Added: {args.name}")

def cmd_list(args):
    habits = load_habits()
    if not habits:
        print("No habits yet.")
        return
    for i, h in enumerate(habits, 1):
        print(format_habit_line(i, h))

def cmd_done(args):
    habits = load_habits()
    status = mark_habit_done(habits, args.index)   # 1-based index in your logic
    if status == "already":
        print("ℹ️ Already marked today.")
    elif status in ("incremented", "reset_to_1"):
        save_habits(habits)
        msg = "Streak incremented." if status == "incremented" else "Streak reset to 1."
        print(f"✅ Marked. {msg}")
    elif status == "bad_index":
        print("❌ Invalid number.")
    else:
        print("❌ Invalid input.")

def cmd_delete(args):
    habits = load_habits()
    status = delete_habit(habits, args.index)  # accepts str|int (1-based)
    if status == "deleted":
        save_habits(habits)
        print("🗑️ Deleted.")
    elif status == "bad_index":
        print("❌ Invalid number.")
    else:
        print("❌ Invalid input.")

def cmd_edit(args):
    """
    Your edit_habit expects 0-based index in our latest version.
    Convert from 1-based CLI index to 0-based for the function.
    """
    habits = load_habits()
    idx0 = args.index - 1
    status = edit_habit(habits, idx0, args.name or "", args.streak or "", args.date or "")
    if status == "edited":
        save_habits(habits)
        print("✏️ Edited.")
    elif status == "nothing":
        print("ℹ️ No changes made.")
    elif status == "invalid_streak":
        print("❌ Invalid streak. Use a non-negative integer.")
    elif status == "invalid_date":
        print("❌ Invalid date. Use DD-MM-YYYY.")
    elif status == "bad_index":
        print("❌ Invalid number.")
    else:
        print("❌ Unknown error.")

def cmd_dashboard(args):
    habits = load_habits()
    if not habits:
        print("No habits yet.")
        return
    computed = get_dashboard(habits)
    for row in computed:
        print(format_dashboard_line(row))

def build_parser():
    p = argparse.ArgumentParser(prog="habits", description="Habit Tracker (subcommands)")
    sub = p.add_subparsers(dest="command", required=True)

    # habits add "Pray Daily"
    sp_add = sub.add_parser("add", help="Add a new habit")
    sp_add.add_argument("name", help="Habit name (quoted if contains spaces)")
    sp_add.set_defaults(func=cmd_add)

    # habits list
    sp_list = sub.add_parser("list", help="List all habits")
    sp_list.set_defaults(func=cmd_list)

    # habits done 2
    sp_done = sub.add_parser("done", help="Mark habit as done (by 1-based index)")
    sp_done.add_argument("index", type=int, help="Habit number (1-based)")
    sp_done.set_defaults(func=cmd_done)

    # habits delete 3
    sp_delete = sub.add_parser("delete", help="Delete habit (by 1-based index)")
    sp_delete.add_argument("index", type=int, help="Habit number (1-based)")
    sp_delete.set_defaults(func=cmd_delete)

    # habits edit 1 --name "Pray Daily" --streak 5 --date 21-08-2025
    sp_edit = sub.add_parser("edit", help="Edit habit fields")
    sp_edit.add_argument("index", type=int, help="Habit number (1-based)")
    sp_edit.add_argument("--name", help="New name")
    sp_edit.add_argument("--streak", help="New streak (non-negative int)")
    sp_edit.add_argument("--date", help="New last-done date (DD-MM-YYYY)")
    sp_edit.set_defaults(func=cmd_edit)

    # habits dashboard
    sp_dash = sub.add_parser("dashboard", help="Show computed dashboard")
    sp_dash.set_defaults(func=cmd_dashboard)

    return p

def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()

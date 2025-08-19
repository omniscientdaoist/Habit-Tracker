from habit import (
    add_habit, mark_habit_done,
    get_dashboard, format_dashboard_line, format_habit_line,
    delete_habit
)
from save import load_habits, save_habits

def main():
    habits = load_habits()

    while True:
        print("\n=== Habit Tracker ===")
        print("1) Add habit")
        print("2) List habits")
        print("3) Mark habit as done")
        print("4) Dashboard")
        print("5) Delete habit")
        print("6) Exit")
        choice = input("Choose (1-6): ").strip()

        if choice == "1":
            name = input("Habit name: ").strip()
            if not name:
                print("❌ Name cannot be empty.")
                continue
            habits.append(add_habit(name))
            save_habits(habits)
            print("✅ Habit added.")

        elif choice == "2":
            if not habits:
                print("No habits yet.")
                continue
            print("\nYour habits:")
            for i, h in enumerate(habits, 1):
                print(format_habit_line(i, h))

        elif choice == "3":
            if not habits:
                print("No habits yet.")
                continue
            for i, h in enumerate(habits, 1):
                print(format_habit_line(i, h))
            idx = input("Enter habit number: ").strip()
            status = mark_habit_done(habits, idx)
            if status == "already":
                print("ℹ️ Already marked today.")
            elif status == "incremented":
                print("✅ Marked. Streak incremented.")
                save_habits(habits)
            elif status == "reset_to_1":
                print("✅ Marked. Streak reset to 1.")
                save_habits(habits)
            elif status == "bad_index":
                print("❌ Invalid number.")
            else:
                print("❌ Invalid input.")

        elif choice == "4":
            if not habits:
                print("No habits yet.")
                continue
            computed = get_dashboard(habits)
            print("\n=== Dashboard ===")
            for row in computed:
                print(format_dashboard_line(row))
        
        elif choice == "5":
            if not habits:
                print("No habits yet.")
                continue

            for i, h in enumerate(habits, 1):
                print(format_habit_line(i, h))

            user_input = input("Enter habit number: ").strip()
            status = delete_habit(habits, user_input)

            if status == "deleted":
                print("✅ Habit deleted.")
                save_habits(habits)
            elif status == "bad_index":
                print("❌ Invalid number.")
            elif status == "invalid_input":
                print("❌ Invalid input.")
            else:
                # fallback, shouldn't happen
                print("❌ Unknown error.")

        elif choice == "6":
            print("👋 Goodbye.")
            break

        else:
            print("❌ Invalid option.")

if __name__ == "__main__":
    main()

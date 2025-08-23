from habit import (
    add_habit, mark_habit_done,
    get_dashboard, format_dashboard_line, format_habit_line,
    delete_habit, edit_habit
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
        print("6) Edit habit")
        print("7) Exit")
        choice = input("Choose (1-7): ").strip()

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
            status, removed = delete_habit(habits, user_input)

            if status == "deleted":
                print(f"✅ {removed['name']} habit deleted.")
                save_habits(habits)
            elif status == "bad_index":
                print("❌ Invalid number.")
            elif status == "invalid_input":
                print("❌ Invalid input.")
            else:
                # fallback, shouldn't happen
                print("❌ Unknown error.")


        elif choice == "6":  
            if not habits:
                print("No habits yet.")
                continue

            for i, h in enumerate(habits, 1):
                print(format_habit_line(i, h))

            user_input = input("Enter habit number to edit: ").strip()

            # quick index check BEFORE asking for new name
            try:
                idx = int(user_input) - 1
            except ValueError:
                print("❌ Invalid input.")
                continue

            if idx < 0 or idx >= len(habits):
                print("❌ Invalid number.")
                continue

            # only here we know the index is valid
            new_name = input("Enter new name or leave blank to skip: ").strip()

            new_streak = input("Enter new streak or leave blank to skip: ").strip()
            
            new_date = input("Enter new date e.g. 21-08-2025 (or leave blank to skip): ").strip()
            
            status = edit_habit(habits, idx, new_name, new_streak, new_date)

            if status == "edited":
                print(f"✏️ Habit edited.")
                save_habits(habits)
            elif status == "nothing":
                print("❌ No changes have been made.")


        elif choice == "7":
            print("👋 Goodbye.")
            break

        else:
            print("❌ Invalid option.")

if __name__ == "__main__":
    main()

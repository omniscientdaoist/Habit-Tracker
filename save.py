import json


def load_habits(filename="habits.json"):
    try:
        with open(filename, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []  # no file yet: start fresh
    except json.JSONDecodeError:
        print("⚠️ habits.json is corrupted or empty. Starting fresh.")
        return []


def save_habits(habits, filename="habits.json"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(habits, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Failed to save habits: {e}")

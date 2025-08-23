from datetime import datetime, timedelta

# --- Creation ---

def add_habit(name: str) -> dict:
    return {"name": name, "streak": 0, "last_done": None}

# --- Marking logic ---

def mark_habit_done(habits: list, index: str | int) -> str:
    """
    Mutates 'habits' in place.
    Returns a status string: 'already', 'incremented', 'reset_to_1',
    'bad_index', or 'invalid_input'.
    """
    # index safety
    try:
        idx = int(index) - 1
        if idx < 0 or idx >= len(habits):
            return "bad_index"
    except ValueError:
        return "invalid_input"

    habit = habits[idx]
    today = datetime.today().date()
    yesterday = today - timedelta(days=1)

    last_done_date = None
    if habit.get("last_done"):
        try:
            last_done_date = datetime.strptime(habit["last_done"], "%d-%m-%Y").date()
        except ValueError:
            last_done_date = None  # treat invalid legacy values as never done

    if last_done_date == today:
        return "already"

    if last_done_date == yesterday:
        habit["streak"] += 1
        habit["last_done"] = today.strftime("%d-%m-%Y")
        return "incremented"

    # first time or gap → reset streak to 1
    habit["streak"] = 1
    habit["last_done"] = today.strftime("%d-%m-%Y")
    return "reset_to_1"

# --- Computed dashboard ---

def days_since(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        date_obj = datetime.strptime(date_str, "%d-%m-%Y").date()
    except ValueError:
        return None
    today = datetime.today().date()
    return (today - date_obj).days  # 0 today, 1 yesterday, N otherwise

def compute_habit(habit: dict) -> dict:
    N = days_since(habit.get("last_done"))
    stale = (N is not None) and (N >= 2)
    return {
        "name": habit.get("name", "Untitled"),
        "streak": habit.get("streak", 0),
        "days_since": N,
        "stale": stale
    }

def get_dashboard(habits: list) -> list[dict]:
    computed = [compute_habit(h) for h in habits]

    def sort_key(h: dict):
        # stale first (False < True so invert), then by days_since desc, then streak desc
        # None days_since → -1 so NEW shows last in days ordering
        days = h["days_since"] if h["days_since"] is not None else -1
        return (not h["stale"], -days, -h["streak"])

    return sorted(computed, key=sort_key)

# --- Pretty printing helpers (pure presentation) ---

def format_habit_line(index: int, habit: dict) -> str:
    """For the raw list view (no computed fields)."""
    name = habit.get("name", "Untitled")
    streak = habit.get("streak", 0)
    last_done = habit.get("last_done") or "Never"
    return f"{index}. {name} — Streak {streak}, Last done {last_done}"

def format_dashboard_line(h: dict) -> str:
    """For the dashboard computed view."""
    name = h["name"]
    streak = h["streak"]
    N = h["days_since"]

    if N is None:
        badge = "🆕 NEW  "
        when = "never done"
    elif N == 0:
        badge = "✅ TODAY"
        when = "done today"
    elif N >= 2:
        badge = "🔥 STALE"
        when = f"last done {N} day(s) ago"
    else:  # N == 1
        badge = "⌛ ACTIVE"
        when = "last done yesterday"

    return f"{badge} | {name} — streak {streak} | {when}"


def delete_habit(habits: list[dict], index: str | int) -> tuple[str, dict | None]:
    """
    Removes one habit (1-based index).
    Mutates `habits` in place.
    Returns: 'deleted', 'bad_index', or 'invalid_input'.
    """
    try:
        idx = int(index) - 1
    except ValueError:
        return "invalid_input"

    if idx < 0 or idx >= len(habits):
        return "bad_index"

    removed = habits.pop(idx)
    return "deleted", removed


def edit_habit(habits: list[dict], index: str | int, name: str, streak: int | str, date: str) -> str:
    """
    Edit fields of a single habit.

    Args:
        habits (list[dict]): The list of habit dictionaries to update.
        index (int): Zero-based index of the habit to edit (validated in the menu).
        name (str): New name for the habit, or empty string "" to skip.
        streak (str): New streak value as a string (will be cast to int), or "" to skip.
        date (str): New date string in format "DD-MM-YYYY", or "" to skip.

    Behavior:
        - Only updates fields if corresponding inputs are non-empty.
        - Validates `streak` to ensure it is an integer ≥ 0.
        - Validates `date` format using datetime.strptime.

    Returns:
        str: One of the following status codes:
            - "edited": At least one field was successfully updated.
            - "nothing": No changes were requested (all inputs blank).
            - "invalid_streak": Provided streak was not a valid non-negative integer.
            - "invalid_date": Provided date was not in the correct format.

    Side Effects:
        Mutates the `habits` list in place by updating the selected habit.
    """

    if not name and not streak and not date:
        return "nothing"
    
    habit = habits[index]

    if name:
        habit["name"] = name
    
    if streak:
        try:
            valid_streak = int(streak)
        except ValueError:
            return "invalid_streak"
        if valid_streak >= 0:
            habit["streak"] = valid_streak
        else:
            return "invalid_streak"

    if date:
        try:
            valid_date = datetime.strptime(date, "%d-%m-%Y").date()
            habit["last_done"] = valid_date.strftime("%d-%m-%Y")
        except ValueError:
            return "invalid_date"
    
    return "edited" 



    

        
# habit_tracker/repo.py
from __future__ import annotations

import sqlite3


class HabitRepo:
    """
    Minimal SQLite repository for habits.
    Responsible ONLY for database reads/writes — no business logic.
    """

    def __init__(self, db_path: str = "habits.db"):
        self.db_path = db_path
        # connect to DB file; row_factory lets us access columns by name
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        """
        Configure the connection and ensure the 'habits' table exists.
        PRAGMAs:
          - foreign_keys ON: good practice (future-proof)
          - journal_mode WAL: better concurrent read/write behavior
        """
        # each 'with self.conn:' block is a transaction (commit/rollback)
        with self.conn:
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.conn.execute("PRAGMA journal_mode = WAL;")
            self.conn.execute("PRAGMA synchronous = NORMAL;")
            self.conn.executescript(
                """
               CREATE TABLE IF NOT EXISTS habits (
                 id        INTEGER PRIMARY KEY AUTOINCREMENT,
                 name      TEXT    NOT NULL,
                 streak    INTEGER NOT NULL DEFAULT 0,
                 last_done TEXT    NULL
               );
               CREATE TABLE IF NOT EXISTS completions (
                 habit_id INTEGER NOT NULL,
                 done_on  TEXT    NOT NULL,
                 PRIMARY KEY (habit_id, done_on),
                 FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
               );
               CREATE INDEX IF NOT EXISTS idx_completions_done_on
                ON completions(done_on);
               CREATE INDEX IF NOT EXISTS idx_completions_habit
                ON completions(habit_id, done_on);
               """
            )

    # ---------- CRUD methods ----------

    def fetch_all(self) -> list[dict]:
        """Return all habits as a list of dicts (ordered by id)."""
        cur = self.conn.execute("SELECT id, name, streak, last_done FROM habits ORDER BY id ASC;")
        return [dict(row) for row in cur.fetchall()]

    def insert(self, name: str, streak: int = 0, last_done: str | None = None) -> int:
        """Insert one habit; return its new integer id."""
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO habits (name, streak, last_done) VALUES (?, ?, ?);",
                (name, streak, last_done),
            )
            return cur.lastrowid  # sqlite gives us the new row id

    def update(
        self,
        habit_id: int,
        *,
        name: str | None = None,
        streak: int | None = None,
        last_done: str | None = None,
    ) -> None:
        """
        Update any subset of fields. If nothing provided, this is a no-op.
        We build the SQL dynamically but keep it safe with placeholders (?) and params.
        """
        fields = []
        params = []

        if name is not None:
            fields.append("name = ?")
            params.append(name)
        if streak is not None:
            fields.append("streak = ?")
            params.append(streak)
        if last_done is not None:
            fields.append("last_done = ?")
            params.append(last_done)

        if not fields:
            return  # nothing to update

        params.append(habit_id)
        sql = f"UPDATE habits SET {', '.join(fields)} WHERE id = ?;"

        with self.conn:
            self.conn.execute(sql, params)

    def delete(self, habit_id: int) -> None:
        """Delete a habit by id."""
        with self.conn:
            self.conn.execute("DELETE FROM habits WHERE id = ?;", (habit_id,))

    def close(self) -> None:
        self.conn.close()

    # optional: context manager support → with HabitRepo(path) as repo:
    def __enter__(self) -> HabitRepo:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def add_completion(self, habit_id: int, done_on: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT OR IGNORE INTO completions (habit_id, done_on) VALUES (?, ?);",
                (habit_id, done_on),
            )

    def fetch_completions(self, habit_id: int) -> list[dict]:
        cur = self.conn.execute(
            "SELECT done_on FROM completions WHERE habit_id = ? ORDER BY done_on ASC;",
            (habit_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    def has_completion_on(self, habit_id: int, date_str: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM completions WHERE habit_id = ? AND done_on = ? LIMIT 1;",
            (habit_id, date_str),
        )
        return cur.fetchone() is not None

    def delete_completion(self, habit_id: int, date_str: str) -> bool:
        with self.conn:
            cur = self.conn.execute(
                "DELETE FROM completions WHERE habit_id = ? AND done_on = ?;",
                (habit_id, date_str),
            )
        return cur.rowcount > 0

    def fetch_completions_between(self, start_date: str, end_date: str) -> list[dict]:
        """
        Return rows of {habit_id, done_on} where start_date <= done_on <= end_date.
        Dates are strings 'DD-MM-YYYY' (your DateFmt) stored as TEXT.
        """
        cur = self.conn.execute(
            """
            SELECT habit_id, done_on
            FROM completions
            WHERE done_on >= ? AND done_on <= ?
            ORDER BY done_on ASC, habit_id ASC;
            """,
            (start_date, end_date),
        )
        return [dict(r) for r in cur.fetchall()]

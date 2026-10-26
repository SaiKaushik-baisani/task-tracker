"""Small SQLite helpers for storing tasks."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


DEFAULT_DB_PATH = Path(__file__).parent / "data" / "tasks.db"
LEGACY_DB_PATH = Path(__file__).parent / "tasks.db"
DB_PATH = DEFAULT_DB_PATH


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Open a connection and close it after the database work is complete."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def _migrate_legacy_database() -> None:
    if (
        DB_PATH != DEFAULT_DB_PATH
        or DB_PATH.exists()
        or not LEGACY_DB_PATH.is_file()
    ):
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(LEGACY_DB_PATH)
    try:
        destination = sqlite3.connect(DB_PATH)
        try:
            source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()


def initialize_database() -> None:
    """Create the tasks table if it does not exist yet."""
    _migrate_legacy_database()
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def _task_from_row(row: sqlite3.Row) -> dict[str, int | str | bool]:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


# INSERT: add a new task and return the saved task.
def create_task(title: str) -> dict[str, int | str | bool]:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title) VALUES (?)",
            (title,),
        )
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return _task_from_row(row)


# SELECT: return every task, newest first.
def list_tasks() -> list[dict[str, int | str | bool]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, title, done FROM tasks ORDER BY id DESC"
        ).fetchall()
    return [_task_from_row(row) for row in rows]


# SELECT: find one task by its ID, or return None when it is missing.
def get_task(task_id: int) -> dict[str, int | str | bool] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    if row is None:
        return None
    return _task_from_row(row)


# UPDATE: replace a task's title and done state.
def update_task(
    task_id: int,
    title: str,
    done: bool,
) -> dict[str, int | str | bool] | None:
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (title, int(done), task_id),
        )
        if cursor.rowcount == 0:
            return None
        row = connection.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    return _task_from_row(row)


# DELETE: remove one task and report whether it existed.
def delete_task(task_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,),
        )
    return cursor.rowcount > 0

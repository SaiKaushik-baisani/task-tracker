from collections.abc import Iterator
from pathlib import Path
import sqlite3

import pytest
from fastapi.testclient import TestClient

import database
from main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "data" / "test_tasks.db")
    with TestClient(app) as test_client:
        yield test_client


def test_create_and_list_tasks(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "Learn CRUD"})

    assert response.status_code == 201
    task = response.json()
    assert task["title"] == "Learn CRUD"
    assert task["done"] is False
    assert set(task) == {"id", "title", "done"}
    assert task["id"] > 0
    assert client.get("/tasks").json() == [task]


def test_home_serves_task_tracker(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<title>Task Tracker</title>" in response.text


def test_tasks_are_listed_newest_first(client: TestClient) -> None:
    first = client.post("/tasks", json={"title": "First"}).json()
    second = client.post("/tasks", json={"title": "Second"}).json()

    assert client.get("/tasks").json() == [second, first]


@pytest.mark.parametrize("title", ["", "   ", "x" * 101])
def test_create_rejects_invalid_title(client: TestClient, title: str) -> None:
    response = client.post("/tasks", json={"title": title})

    assert response.status_code == 422


def test_get_task_and_missing_task(client: TestClient) -> None:
    task = client.post("/tasks", json={"title": "Read the docs"}).json()

    assert client.get(f"/tasks/{task['id']}").json() == task
    assert client.get("/tasks/999").status_code == 404


def test_update_task_and_missing_task(client: TestClient) -> None:
    task = client.post("/tasks", json={"title": "First title"}).json()

    response = client.put(
        f"/tasks/{task['id']}",
        json={"title": "Updated title", "done": True},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated title"
    assert response.json()["done"] is True
    assert set(response.json()) == {"id", "title", "done"}
    assert client.get(f"/tasks/{task['id']}").json() == response.json()
    assert client.put(
        "/tasks/999",
        json={"title": "Missing task", "done": False},
    ).status_code == 404


def test_delete_task_and_missing_task(client: TestClient) -> None:
    task = client.post("/tasks", json={"title": "Remove me"}).json()

    assert client.delete(f"/tasks/{task['id']}").status_code == 204
    assert client.get(f"/tasks/{task['id']}").status_code == 404
    assert client.delete("/tasks/999").status_code == 404


def test_initialize_migrates_existing_tasks_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "data" / "tasks.db"
    legacy_db_path = tmp_path / "tasks.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    monkeypatch.setattr(database, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr(database, "LEGACY_DB_PATH", legacy_db_path)
    connection = sqlite3.connect(legacy_db_path)
    try:
        connection.execute(
            """
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                legacy_field TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            "INSERT INTO tasks (title, done, legacy_field) VALUES (?, ?, ?)",
            ("Existing task", 1, "Legacy value"),
        )
        connection.commit()
    finally:
        connection.close()

    database.initialize_database()

    assert legacy_db_path.is_file()
    assert database.get_task(1) == {
        "id": 1,
        "title": "Existing task",
        "done": True,
    }
    created = database.create_task("New task")
    updated = database.update_task(created["id"], "Updated task", False)
    assert updated == {**created, "title": "Updated task"}

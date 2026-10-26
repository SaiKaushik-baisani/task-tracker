# Task Tracker

A small CRUD app built with FastAPI, SQLite's built-in `sqlite3` module, Pydantic, and plain HTML/JavaScript. It stores tasks in `data/tasks.db` beside `main.py` and creates the data directory and table automatically when the server starts.

## Run locally

From the project folder, create and activate a virtual environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can instead run the environment's Python directly as `.\.venv\Scripts\python.exe`.

Install the dependencies and start the server:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open <http://127.0.0.1:8000> in a browser. The interactive API documentation is at <http://127.0.0.1:8000/docs>.

## Run with Docker Compose

From the project folder, build and start the container:

```powershell
docker compose up --build
```

The Compose named volume persists the SQLite database at `/app/data` without mounting over the application files. Open <http://127.0.0.1:8000> or <http://127.0.0.1:8000/docs>. Stop the container with `docker compose down`. Do not use `docker compose down -v` unless you intend to delete the persisted database volume.

## Run tests

With the virtual environment active:

```powershell
python -m pytest
```

The tests use a temporary SQLite database, so they do not change the app's `tasks.db`.

## How CRUD requests work

The browser builds a JSON request when you add, edit, toggle, or delete a task. FastAPI routes in `main.py` receive it; Pydantic models in `models.py` validate the title and update fields. The route calls a helper in `database.py`, which opens SQLite and runs a parameterized SQL statement (`?` placeholders). The result (or a 404 for a missing task) is returned as JSON or a no-content response. After a successful action, the page fetches `GET /tasks` again and redraws the list.

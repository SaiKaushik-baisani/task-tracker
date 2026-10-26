"""FastAPI routes for the Task Tracker."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import database
from models import TaskCreate, TaskRead, TaskUpdate


BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    database.initialize_database()
    yield


app = FastAPI(title="Task Tracker", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


# INSERT: store a new task through the database helper.
@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate) -> dict[str, int | str | bool]:
    return database.create_task(task.title)


# SELECT: retrieve the full task list through the database helper.
@app.get("/tasks", response_model=list[TaskRead])
def list_tasks() -> list[dict[str, int | str | bool]]:
    return database.list_tasks()


# SELECT: retrieve one task through the database helper.
@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int) -> dict[str, int | str | bool]:
    task = database.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


# UPDATE: change a task through the database helper.
@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task: TaskUpdate) -> dict[str, int | str | bool]:
    updated_task = database.update_task(
        task_id,
        task.title,
        task.done,
    )
    if updated_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return updated_task


# DELETE: remove a task through the database helper.
@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> Response:
    if not database.delete_task(task_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

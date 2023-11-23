"""Main of todo app
"""
from loguru import logger

from fastapi import FastAPI, Request, Depends, Form, status, Response, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import Annotated
from database import init_db, get_db, Session
import models

init_db()

# pylint: disable=invalid-name
templates = Jinja2Templates(directory="templates")

app = FastAPI()

logger = logger.opt(colors=True)
# pylint: enable=invalid-name

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def home(request: Request, database: Session = Depends(get_db)):
    """Main page with todo list
    """
    logger.info("In home")
    todos = database.query(models.Todo).order_by(models.Todo.id.desc())
    return templates.TemplateResponse("index.html", {"request": request, "todos": todos})


@app.post("/add", status_code=status.HTTP_201_CREATED)
async def todo_add(request: Request,
                   response: Response,
                   task: Annotated[str, Form(max_length=500)] = None,
                   database: Session = Depends(get_db)):
    """Add new todo
    """
    if task is None or task.replace(" ", "") == "" or task == "":
        response.status_code = status.HTTP_411_LENGTH_REQUIRED
        return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)
    todo = models.Todo(task=task)
    logger.info(f"Creating todo: {todo}")
    database.add(todo)
    database.commit()
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


@app.get("/edit/{todo_id}")
async def todo_get(request: Request,
                   todo_id: int, database: Session = Depends(get_db)):
    """Get todo
    """
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    logger.info(f"Getting todo: {todo}")
    return templates.TemplateResponse("edit.html", {"request": request, "todo": todo})


@app.post("/edit/{todo_id}", status_code=status.HTTP_202_ACCEPTED)
async def todo_edit(
        request: Request,
        response: Response,
        todo_id: int,
        task:  Annotated[str, Form(max_length=500)] = None,
        completed: bool = Form(False),
        database: Session = Depends(get_db)):
    """Edit todo
    """
    if task is None or task.replace(" ", "") == "":
        response.status_code = status.HTTP_411_LENGTH_REQUIRED
        return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    logger.info(f"Editting todo: {todo}")
    todo.task = task
    todo.completed = completed
    database.commit()
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


@app.get("/delete/{todo_id}")
async def todo_delete(request: Request,
                      todo_id: int,
                      database: Session = Depends(get_db)):
    """Delete todo
    """
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    logger.info(f"Deleting todo: {todo}")
    database.delete(todo)
    database.commit()
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

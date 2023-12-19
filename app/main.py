"""Main of todo app
"""
from loguru import logger

from fastapi import FastAPI, Request, Depends, Form, status, Response, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import Annotated
from database import init_db, get_db, Session
import models

from tags import TodoTags

init_db()

# pylint: disable=invalid-name
templates = Jinja2Templates(directory="templates")

app = FastAPI()

logger = logger.opt(colors=True)
# pylint: enable=invalid-name

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def home(request: Request,
               database: Session = Depends(get_db),
               limit: int = 5,
               skip: int = 1):
    """Main page with todo list
    """
    logger.info("In home")
    count_todos = database.query(models.Todo).count()
    count_pages = int(count_todos / limit)
    if count_todos < 10:
        todos = database.query(models.Todo).order_by(models.Todo.id.desc())
        return templates.TemplateResponse("index.html", {"request": request, "todos": todos,
                                                         "limit": limit, "skip": skip,
                                                         "count_pages": 0, "types": TodoTags})
    if count_pages * limit != count_todos:
        count_pages += 1
    if skip > count_pages:
        todos = database.query(models.Todo).order_by(models.Todo.id.desc()).offset(0).limit(limit)
        return templates.TemplateResponse("index.html", {"request": request, "todos": todos,
                                                         "limit": limit, "skip": skip,
                                                         "count_pages": count_pages, "types": TodoTags})
    todos = database.query(models.Todo).order_by(models.Todo.id.desc()).offset(limit * skip).limit(limit)
    return templates.TemplateResponse("index.html", {"request": request, "todos": todos,
                                                     "limit": limit, "skip": skip,
                                                     "count_pages": count_pages, "types": TodoTags})


@app.post("/add")
async def todo_add(request: Request,
                   title: Annotated[str, Form(max_length=50)] = None,
                   type: Annotated[str, Form()] = "Education",
                   details: Annotated[str, Form(max_length=500)] = None,
                   database: Session = Depends(get_db)):
    """Add new todo
    """
    if title is None:
        return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_301_MOVED_PERMANENTLY)
    todo = models.Todo(title=title, details=details, type=type)
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
        todo_id: int,
        title: Annotated[str, Form(max_length=50)] = None,
        details: Annotated[str, Form(max_length=500)] = None,
        completed: bool = Form(False),
        database: Session = Depends(get_db)):
    """Edit todo
    """
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if todo is not None and title is not None and title.replace(" ", "") != "":
        todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
        logger.info(f"Editting todo: {todo}")
        todo.title = title
        todo.details = details
        todo.completed = completed
        database.commit()
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


@app.delete("/delete/{todo_id}", status_code=status.HTTP_202_ACCEPTED)
async def todo_delete(request: Request,
                      todo_id: int,
                      database: Session = Depends(get_db)):
    """Delete todo
    """
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if todo is not None:
        logger.info(f"Deleting todo: {todo}")
        database.delete(todo)
        database.commit()
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


@app.post("/change_status/{todo_id}", status_code=status.HTTP_202_ACCEPTED)
async def todo_change_status(request: Request,
                             todo_id: int,
                             database: Session = Depends(get_db)):
    """Change todo status on home page
    """
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if todo is not None:
        if todo.completed is True:
            todo.completed = False
            logger.info(f"Editting status: {todo} to not Done")
        else:
            todo.completed = True
            logger.info(f"Editting status: {todo} to Done")
        database.commit()
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

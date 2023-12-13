"""Main of todo app
"""
import random

from loguru import logger
from visualization import visualize
from fastapi import FastAPI, Request, Depends, Form, status, Response, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import Annotated
from database import init_db, get_db, Session
import models
import pandas as pd
import openpyxl
import xlrd
from datetime import date
import os
from os import path
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
    """Main page with todo list"""
    return templates.TemplateResponse("index.html", {"request": request, "types": TodoTags})


@app.get("/list")
async def list_todo(request: Request,
               database: Session = Depends(get_db),
               limit: int = 5,
               skip: int = 1):
    logger.info("Todo list")
    count_todos = database.query(models.Todo).count()
    count_pages = int(count_todos / limit)
    if count_todos < 10:
        todos = database.query(models.Todo).order_by(models.Todo.id.desc())
        return templates.TemplateResponse("list.html", {"request": request, "todos": todos,
                                                         "limit": limit, "skip": skip,
                                                         "count_pages": 0, "types": TodoTags})
    if count_pages * limit != count_todos:
        count_pages += 1
    if skip > count_pages:
        todos = database.query(models.Todo).order_by(models.Todo.id.desc()).offset(0).limit(limit)
        return templates.TemplateResponse("list.html", {"request": request, "todos": todos,
                                                         "limit": limit, "skip": skip,
                                                         "count_pages": count_pages, "types": TodoTags})
    todos = database.query(models.Todo).order_by(models.Todo.id.desc()).offset(limit * skip).limit(limit)
    return templates.TemplateResponse("list.html", {"request": request, "todos": todos,
                                                     "limit": limit, "skip": skip,
                                                     "count_pages": count_pages, "types": TodoTags})


@app.post("/add", status_code=status.HTTP_202_ACCEPTED)
async def todo_add(request: Request,
                   title: Annotated[str, Form(max_length=50)] = None,
                   type: Annotated[str, Form()] = "Education",
                   details: Annotated[str, Form(max_length=500)] = None,
                   database: Session = Depends(get_db)):
    """Add new todo
    """
    if title is not None and title.replace(" ", "") != "" or title == "":
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

        if completed is False:
            todo.date_completion="-1"
        else:
            todo.date_completion=date.today()
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
            todo.date_completion = "-1"
            logger.info(f"Editting status: {todo} to not Done")
        else:
            todo.completed = True
            logger.info(f"Editting status: {todo} to Done")
            todo.date_completion = date.today()
        database.commit()
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


@app.post("/generate")
async def generate_todo(request: Request,
                        database: Session = Depends(get_db),
                        count: Annotated[int, None] = 10):
    titles = ["пахтальщик", "шкипер", "усвоение", "недовыручка", "печение", "двухголосие", "уламывание", "решето",
              "рамщик", "дрожина", "акушер", "грушанка", "маргарин", "хлорофилл", "штатив", "осмий", "повар", "закладка",
              "оскопление", "прибивание"]
    types = ["Education", "Personal", "Plan"]

    for i in range(0, count):
        title = titles[random.randint(0, 19)] + " " + titles[random.randint(0, 19)]
        type = types[random.randint(0, 2)]
        await todo_add(request, title, type, None, database)
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


@app.get("/export")
async def export(request: Request,database: Session = Depends(get_db)):
    logger.info("Exporting")
    todos = database.query(models.Todo)
    lst = []
    for todo in todos:
        lst.append({
            "id":todo.id,
            "title": todo.title,
            "details": todo.details,
            "completed": todo.completed,
            "tag": todo.type,
            "date_creation":todo.date_creation,
            "date_completion":todo.date_completion
        })
    df = pd.DataFrame(data=lst)
    df.to_excel("Data.xlsx")
    return FileResponse(path='Data.xlsx', filename='Export.xlsx', media_type='application/octet-stream')


@app.get("/visualization")
async def visualization(request: Request,
               database: Session = Depends(get_db),
               limit: int = 5,
               skip: int = 1):
    logger.info("Visualizating")
    if path.exists("Visualization.png"):
        os.remove("Visualization.png")
    if path.exists("Data.xlsx"):
        os.remove("Data.xlsx")
    count_todos = database.query(models.Todo).count()
    count_pages = int(count_todos / limit)
    if count_todos < 10:
        todos = database.query(models.Todo).order_by(models.Todo.id.desc())
        return templates.TemplateResponse("visualization.html", {"request": request, "todos": todos,
                                                         "limit": limit, "skip": skip,
                                                         "count_pages": 0, "types": TodoTags})
    if count_pages * limit != count_todos:
        count_pages += 1
    if skip > count_pages:
        todos = database.query(models.Todo).order_by(models.Todo.id.desc()).offset(0).limit(limit)
        return templates.TemplateResponse("visualization.html", {"request": request, "todos": todos,
                                                         "limit": limit, "skip": skip,
                                                         "count_pages": count_pages, "types": TodoTags})
    todos = database.query(models.Todo).order_by(models.Todo.id.desc()).offset(limit * skip).limit(limit)
    return templates.TemplateResponse("visualization.html", {"request": request, "todos": todos,
                                                     "limit": limit, "skip": skip,
                                                     "count_pages": count_pages, "types": TodoTags})


@app.get("/visualize/{todo_id}")
async def vis(request: Request,todo_id:int,database: Session = Depends(get_db)):
    todo_title = database.query(models.Todo.title).filter(models.Todo.id == todo_id).first()
    title=str(todo_title).split("\'")[1]
    visualize(title,"Visualization.png")
    return FileResponse(path='Visualization.png', filename='Visualization.png', media_type='image/png')


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

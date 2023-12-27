"""Main of todo app
"""
import io
import random

import numpy
from loguru import logger
from matplotlib import pyplot as plt
from wordcloud import WordCloud

from support import visualize
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
# import openpyxl
# import xlrd
from datetime import date, datetime
import os
from os import path
from tags import TodoTags, Users, Source

from sqlalchemy import Date

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
    count_cha = database.query(models.Todo).filter(models.Todo.fullname == "2021-3-26-cha").filter(
        models.Todo.completed == True).count()
    count_zva = database.query(models.Todo).filter(models.Todo.fullname == "2021-3-04-zva").filter(
        models.Todo.completed == True).count()
    count_pro = database.query(models.Todo).filter(models.Todo.fullname == "2021-3-12-pro").filter(
        models.Todo.completed == True).count()
    return templates.TemplateResponse("index.html",
                                      {"request": request, "types": TodoTags, "fullnames": Users, "cha": count_cha,
                                       "zva": count_zva, "pro": count_pro})


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
                   type: Annotated[str, Form()] = TodoTags.education.value,
                   source: Annotated[str, Form()] = Source.source_created.value,
                   details: Annotated[str, Form(max_length=500)] = None,
                   fullname: Annotated[str, Form()] = Users.user1.value,
                   date_creation: Annotated[date, Form()] = date.today(),
                   completed: Annotated[bool, Form()] = False,
                   date_completion: Annotated[date, Form()] = None,
                   database: Session = Depends(get_db),
                   ):
    """Add new todo
    """
    if title is not None and title.replace(" ", "") != "" or title == "":
        print(source)
        todo = models.Todo(title=title,
                           details=details,
                           type=type,
                           source=source,
                           fullname=fullname,
                           completed=completed,
                           date_creation=date_creation,
                           date_completion=date_completion)

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
    return templates.TemplateResponse("edit.html", {"request": request, "todo": todo, "fullnames": Users})


@app.post("/edit/{todo_id}", status_code=status.HTTP_202_ACCEPTED)
async def todo_edit(
        request: Request,
        todo_id: int,
        title: Annotated[str, Form(max_length=50)] = None,
        details: Annotated[str, Form(max_length=500)] = None,
        completed: bool = Form(False),
        fullname: Annotated[str, Form()] = "2021-3-26-cha",
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
        todo.fullname = fullname

        if completed is False:
            todo.date_completion = None
        else:
            todo.date_completion = date.today()
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
            todo.date_completion = None
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
              "рамщик", "дрожина", "акушер", "грушанка", "маргарин", "хлорофилл", "штатив", "осмий", "повар",
              "закладка",
              "оскопление", "прибивание"]
    types = ["Education", "Personal", "Plan"]

    for i in range(0, count):
        title = titles[random.randint(0, 19)] + " " + titles[random.randint(0, 19)]
        type = types[random.randint(0, 2)]
        await todo_add(request=request,
                       title=title,
                       type=title,
                       source=Source.source_generated.value,
                       details=None,
                       database=database)
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


@app.get("/export")
async def export(request: Request, database: Session = Depends(get_db)):
    logger.info("Exporting")
    todos = database.query(models.Todo)
    lst = []
    for todo in todos:
        lst.append({
            "id": todo.id,
            "title": todo.title,
            "details": todo.details,
            "completed": todo.completed,
            "type": todo.type,
            "date_creation": todo.date_creation,
            "date_completion": todo.date_completion,
            "fullname": todo.fullname
        })
    df = pd.DataFrame(data=lst)

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return Response(content=buffer.getvalue(),
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename={}.xlsx"})


@app.post("/upload/{filename}")
async def upload(request: Request,
                 filename: str,
                 database: Session = Depends(get_db)):
    if not path.exists(f"{filename}"):
        logger.info(f"Error! Trying to import not existing file {filename}.")
        return RedirectResponse(url=app.url_path_for("list_todo"), status_code=status.HTTP_301_MOVED_PERMANENTLY)

    df = pd.read_excel(filename,
                       converters={'date_creation': pd.to_datetime,
                                   'date_completion': pd.to_datetime})

    count_str = len(df.title)
    for i in range(0, count_str):
        print(type(df.date_creation[i]))
        print(df.date_creation[i])
        await todo_add(request=request,
                       title=df.title[i],
                       type=df.type[i],
                       source=Source.source_exported.value,
                       details=df.details[i],
                       date_creation=df.date_creation[i],
                       date_completion=df.date_completion[i] if bool(df.completed[i]) is True else None,
                       completed=bool(df.completed[i]),
                       fullname=df.fullname[i],
                       database=database)
    logger.info(f"File {filename} imported.")
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


@app.get("/visualization")
async def visualization(request: Request,
                        database: Session = Depends(get_db),
                        limit: int = 5,
                        skip: int = 1):
    logger.info("Visualization page")
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
async def vis(request: Request, todo_id: int, database: Session = Depends(get_db)):
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()

    wc = WordCloud(width=300, height=300, background_color="white").generate(todo.details)
    plt.axis("off")
    plt.imshow(wc, interpolation="bilinear")

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    return Response(content=buffer.getvalue(),
                    media_type="image/png",
                    headers={"Content-Disposition": f"attachment; filename={todo.title}.png"})


@app.get("/pageFile")
async def page_file(request: Request):
    return templates.TemplateResponse("pageFile.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, Depends, status, Form, UploadFile, HTTPException, Query
from starlette.responses import RedirectResponse, Response, HTMLResponse, StreamingResponse

from typing import Annotated, List, Dict, Any, Optional
import io
import math
import os
import random
from datetime import date, datetime, timedelta
import datetime
from loguru import logger
import gitlab
import pandas as pd
from gitlab import GitlabAuthenticationError
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from wordcloud import WordCloud
from PIL import Image
import imagehash
from pathlib import Path
import markovify
from markovify.text import ParamError
import hashlib

from application.database import get_db, Session
import application.todo.data as data
import application.todo.models as models
import application.login.models as models_login
from application.todo.tags import TodoTags, Users, Source, tags_metadata
from application.login.oauth2 import get_current_user
import application.todo.es as es

logger = logger.opt(colors=True)
# pylint: disable=invalid-name
templates = Jinja2Templates(directory="/application/templates")

router = APIRouter(
    prefix='/todo',
    tags=['Todo'],
)


async def get_todo_list(type: str = None,
                        date: str = None,
                        text: str = None) -> list:
    """Получение заметок по нескольким критериям. Тег, дата, текст (из поля name, text, text_from_file)

    :param type: Тег для поиска, defaults to None
    :type type: str, optional
    :param date: Дата для поиска, defaults to None
    :type date: str, optional
    :param text: Текст для поиска по полям name, text, text_from_file, defaults to None
    :type text: str, optional
    :return: Заметки, найденные по критериям
    :rtype: list
    """
    ids = []
    if type is not None and type != '':
        ids.append(set(es.find_ids_by_tag(type)))
    if date is not None and date != '':
        ids.append(set(es.find_by_date(date)))
    if text is not None and text != '':
        ids.append(set(es.find_by_text(text)))
    if not ids:
        return []
    return list(set.intersection(*ids))

@router.get("/list", tags=["Lists"])
async def list_todo(request: Request,
                    database: Session = Depends(get_db),
                    type: str = None,
                    limit: str = None,
                    skip: str = None,
                    date: str = None,
                    text: str = None):
    """Функция, отвечающая за /list

    :param request: Request
    :type request: Request
    :param database: База данных, defaults to Depends(get_db)
    :type database: Session, optional
    :param type: Тег записи для поиска, defaults to None
    :type type: str, optional
    :param limit: Максимально количество записей на странице, defaults to None
    :type limit: str, optional
    :param skip: Количество пропущенных страниц, defaults to None
    :type skip: str, optional
    :param date: Дата для поиска, defaults to None
    :type date: str, optional
    :param text: Текст для поиска, defaults to None
    :type text: str, optional
    :return: Страница /list
    :rtype: 
    """
    top_10 = []
    try:
        top_10 = es.get_top_10()
    except Exception as e:
        logger(f"Error getting aggregation data: {str(e)}")
        top_10 = []
    todos = list()
    if (type is None or type == '') and (date is None or date == '') and (text is None or text == ''):
        todos = database.query(models.Todo).all()
    else:
        ids = await get_todo_list(type = type, date=date, text=text)
        todos = database.query(models.Todo).filter(models.Todo.id.in_(ids)).order_by(models.Todo.id.desc()).all()
    tags = database.query(models.UsersTags.tag).all()
    count_pages = 1
    skip = "0"
    limit = str(len(todos))
    template_response = templates.TemplateResponse("list.html",
                                                   {
                                                       "request": request,
                                                       "todos": todos,
                                                       "limit": limit,
                                                       "skip": skip,
                                                       "count_pages": count_pages,
                                                       "types": tags, "type": type,
                                                       "top_10": top_10})
    template_response.set_cookie("limit", str(limit))
    template_response.set_cookie("skip", str(skip))
    return template_response


@router.post("/add", tags=["Todo"])
async def todo_add(request: Request,
                   title: Annotated[str, Form(max_length=50)] = None,
                   type: Annotated[str, Form()] = TodoTags.education.value,
                   source: Annotated[str, Form()] = Source.source_created.value,
                   details: Annotated[str, Form(max_length=500)] = None,
                   fullname: Annotated[str, Form()] = "user",
                   date_creation: Annotated[date, Form()] = date.today(),
                   completed: Annotated[bool, Form()] = False,
                   date_completion: Annotated[date, Form()] = None,
                   database: Session = Depends(get_db),
                   current_user: models_login.Users = Depends(get_current_user)
                   ):
    """Add new todo
    """
    if title is not None:
        todo = models.Todo(title=title,
                           details=details,
                           details_hash=hashlib.sha256(details.encode()).hexdigest(),
                           type=type,
                           source=source,
                           fullname=fullname if current_user.name == "admin" else current_user.name,
                           completed=completed,
                           date_creation=date_creation,
                           date_completion=date_completion)
        database.add(todo)
        database.commit()
        database.add(
            models.HistoryList(todo_id=todo.id,
                               event="created",
                               fullname=current_user.name))
        database.commit()
        logger.info(f"Creating todo: {todo}")
        es.indexating_todo(id=todo.id,
                        name=str(title),
                        text=details if details is not None else "", tag=type,
                        date_creation=date_creation)
        es.indexating_todo_activity(id=todo.id,
                      fullname=fullname if current_user.name == "admin" else current_user.name,
                      date_creation=date_creation)
        return {"answer": "ok"}
    return {"answer": "title not found"}


@router.get("/edit/{todo_id}", status_code=status.HTTP_200_OK, tags=["Todo"])
async def todo_get(request: Request,
                   todo_id: int,
                   database: Session = Depends(get_db)):
    """Get todo
    """
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if todo is None:
        logger.info(f"Getting not existing todo: {todo}")
        raise HTTPException(status_code=301)
    path = todo.image_path
    if not os.path.exists(path):
        todo.image_path = str(Path.cwd() / "application" / "static" / "media" / "Empty.png")
    logger.info(f"Getting todo: {todo}")
    other_todos_img = []
    if not todo.hash == "":
        todos = database.query(models.Todo).filter(models.Todo.hash == todo.hash).filter(
            models.Todo.id != todo.id).all()
        for todo_in in todos:
            other_todos_img.append(todo_in.id)

    ids_todos_hash_text = []
    ids_todos_hash_text_from_file = []
    
    if not todo.details_hash == "":
        todos_hash_text = database.query(models.Todo).filter(models.Todo.details_hash == todo.details_hash).filter(
            models.Todo.id != todo.id).all()
        for todo_in in todos_hash_text:
            ids_todos_hash_text.append(todo_in.id)
    if not todo.text_from_file_hash == "":
        todos_hash_text_from_file = database.query(models.Todo).filter(models.Todo.text_from_file_hash == todo.text_from_file_hash).filter(
            models.Todo.id != todo.id).all()
        for todo_in in todos_hash_text_from_file:
            ids_todos_hash_text_from_file.append(todo_in.id)
    
    
    return templates.TemplateResponse("edit.html",
                                      {"request": request, 
                                       "todo_id": todo_id, 
                                       "todo": todo, 
                                       "picture_name": path,
                                       "image": True, 
                                       "fullnames": Users, 
                                       "other_todos_img": other_todos_img,
                                       "ids_todos_hash_text": ids_todos_hash_text,
                                       "ids_todos_hash_text_from_file": ids_todos_hash_text_from_file
                                       })


@router.post("/edit/{todo_id}", status_code=status.HTTP_200_OK, tags=["Todo"])
async def todo_edit(
        request: Request,
        todo_id: int,
        title: Annotated[str, Form(max_length=50)] = None,
        details: Annotated[str, Form(max_length=500)] = None,
        completed: bool = Form(False),
        database: Session = Depends(get_db),
        current_user: models_login.Users = Depends(get_current_user)
):
    """Edit todo
    """
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if todo is not None and title is not None and title.replace(" ", "") != "":
        if current_user.name != todo.fullname and current_user.name != "admin":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
        logger.info(f"Editting todo: {todo}")
        todo.title = title
        todo.details = details
        todo.details_hash = hashlib.sha256(details.encode()).hexdigest()
        todo.completed = completed
        todo.fullname = current_user.name if current_user.name != "admin" else "user"


        if completed is False:
            todo.date_completion = None
        else:
            todo.date_completion = date.today()
        database.add(
            models.HistoryList(todo_id=todo.id,
                               event="edited",
                               fullname=current_user.name))
        database.commit()
        es.editing_todo(id=todo_id, name=str(title), text=details)
        return {"answer": "ok"}
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


@router.get("/history/{todo_id}", status_code=status.HTTP_200_OK, tags=["Todo"])
async def todo_history(
        request: Request,
        todo_id: int,
        database: Session = Depends(get_db)
):
    # Получаем все записи истории для указанного todo_id
    history = (
        database.query(models.HistoryList)
        .filter(models.HistoryList.todo_id == todo_id)
        .order_by(models.HistoryList.time_event.desc())
        .all()
    )
    templates_response = templates.TemplateResponse("history.html", {"request": request, "todo_id": todo_id, "history": history})
    return templates_response


@router.delete("/delete/{todo_id}", tags=["Todo"])
async def todo_delete(request: Request,
                      todo_id: int,
                      database: Session = Depends(get_db),
                      current_user: models_login.Users = Depends(get_current_user)
                      ):
    """Delete todo
    """
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=301)
    if current_user.name != todo.fullname and current_user.name != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    logger.info(f"Deleting todo: {todo}")
    database.delete(todo)
    history = database.query(models.HistoryList).filter(models.HistoryList.todo_id == todo_id).all()
    for item in history:
        database.delete(item)
    database.commit()
    es.deleting_todo(todo_id)
    return {"answer": "ok"}


@router.delete("/delete_all", tags=["Todo"])
async def todo_delete_all(request: Request,
                          database: Session = Depends(get_db),
                          current_user: models_login.Users = Depends(get_current_user)
                          ):
    """Delete all todos"""
    all_todos = database.query(models.Todo).all()
    if current_user.name != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    for todo in all_todos:
        await todo_delete(request=request,
                          todo_id=todo.id,
                          database=database,
                          current_user=current_user)
    return {"answer": "ok"}


@router.delete("/delete_range", tags=["Todo"])
async def todo_delete_range(request: Request,
                            start: str = "0",
                            end: str = "0",
                            type: str = None,
                            database: Session = Depends(get_db),
                            current_user: models_login.Users = Depends(get_current_user),
                            ):
    if start.isdigit() and end.isdigit():
        start, end = int(start), int(end)
    else:
        return {"answer": "nan"}

    if start > end:
        raise HTTPException(status_code=400)
    query = database.query(models.Todo)
    if type is not None and TodoTags.contains(type):
        query = query.filter(models.Todo.type == type)
    count_todos = query.count()
    if start <= 0 or end > count_todos:
        raise HTTPException(status_code=400)

    # todos = database.query(models.Todo).order_by(models.Todo.id.desc()).filter(models.Todo.type == type).all()
    todos = query.order_by(models.Todo.id.desc()).offset(start - 1).limit(end - start + 1)
    if current_user.name != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    for todo in todos:
        database.delete(todo)
        es.deleting_todo(todo.id)

    database.commit()
    return {"answer": "ok"}


@router.post("/change_status/{todo_id}", tags=["Todo"])
async def todo_change_status(request: Request,
                             todo_id: int,
                             database: Session = Depends(get_db),
                             current_user: models_login.Users = Depends(get_current_user)
                             ):
    """Change todo status on home page
    """
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if todo is not None:
        if current_user.name != todo.fullname and current_user.name != "admin":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        if todo.completed is True:
            todo.completed = False
            todo.date_completion = None
            logger.info(f"Editting status: {todo} to not Done")
        else:
            todo.completed = True
            logger.info(f"Editting status: {todo} to Done")
            todo.date_completion = date.today()
        database.commit()
    return {"answer", "ok"}


@router.post("/generate", tags=["Generation"])
async def generate_todo(
        request: Request,
        database: Session = Depends(get_db),
        count: int = Form(default=10),
        current_user: models_login.Users = Depends(get_current_user)
):
    titles = ["пахтальщик", "шкипер", "усвоение", "недовыручка", "печение", "двухголосие", "уламывание", "решето",
              "рамщик", "дрожина", "акушер", "грушанка", "маргарин", "хлорофилл", "штатив", "осмий", "повар",
              "закладка",
              "оскопление", "прибивание"]
    types = ["Education", "Personal", "Plan"]

    if count > 50:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="")

    for i in range(0, count):
        title = titles[random.randint(0, 19)] + " " + titles[random.randint(0, 19)]
        type = types[random.randint(0, 2)]
        await todo_add(request=request,
                       title=title,
                       type=type,
                       source=Source.source_generated.value,
                       fullname="user",
                       details=None,
                       database=database,
                       current_user=current_user
                       )
    return {"answer", "ok"}


@router.post("/generate_20", tags=["Generation"])
async def generate_20_todo(
        request: Request,
        database: Session = Depends(get_db)
):
    titles = ["пахтальщик", "шкипер", "усвоение", "недовыручка", "печение", "двухголосие", "уламывание", "решето",
              "рамщик", "дрожина", "акушер", "грушанка", "маргарин", "хлорофилл", "штатив", "осмий", "повар",
              "закладка",
              "оскопление", "прибивание"]
    types = ["Education", "Personal", "Plan"]

    for i in range(0, 20):
        '''
        type: Annotated[str, Form()] = TodoTags.education.value,
        source: Annotated[str, Form()] = Source.source_created.value,
        details: Annotated[str, Form(max_length=500)] = None,
        fullname: Annotated[str, Form()] = Users.user1.value,
        date_creation: Annotated[date, Form()] = date.today(),
        completed: Annotated[bool, Form()] = False,
        date_completion: Annotated[date, Form()] = None,
        '''
        title = titles[random.randint(0, 19)] + " " + titles[random.randint(0, 19)]
        type = types[random.randint(0, 2)]
        todo = models.Todo(title=title,
                           details=title,
                           type=type,
                           source=Source.source_generated.value,
                           fullname="user",
                           completed=False,
                           date_creation=date.today(),
                           date_completion=None)
        database.add(todo)
        database.commit()
        logger.info(f"Creating todo: {todo}")
        es.indexating_todo(id=todo.id, name=str(title), text=str(title), tag=type, date_creation=date.today())
    return {"answer", "ok"}


@router.get("/export", tags=["Files"])
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
                    headers={"Content-Disposition": f"attachment; filename=Export.xlsx"})


@router.post("/upload/", status_code=status.HTTP_200_OK, tags=["Files"])
async def upload(request: Request,
                 file_input: UploadFile = Form(),
                 database: Session = Depends(get_db),
                 current_user: models_login.Users = Depends(get_current_user)
                 ):
    if file_input.filename.split(".")[-1] != 'xlsx':
        raise HTTPException(status_code=status.HTTP_301_MOVED_PERMANENTLY)
    content = file_input.file.read()
    buffer = io.BytesIO(content)
    df = pd.read_excel(buffer,
                       converters={'date_creation': pd.to_datetime,
                                   'date_completion': pd.to_datetime})

    count_str = len(df.title)
    for i in range(0, count_str):
        await todo_add(request=request,
                       title=df.title[i],
                       type=df.type[i],
                       source=Source.source_exported.value,
                       details=df.details[i] if str(df.details[i]) != "nan" else "",
                       date_creation=df.date_creation[i],
                       date_completion=df.date_completion[i] if bool(df.completed[i]) is True else None,
                       completed=bool(df.completed[i]),
                       fullname=df.fullname[i],
                       database=database,
                       current_user=current_user)
    logger.info(f"File {file_input.filename} imported.")
    database.add(models.ImportedFiles(file_name=file_input.filename))
    database.commit()
    return {"answer": "ok"}


@router.get("/visualization", tags=["Lists"])
async def visualization(request: Request,
                        database: Session = Depends(get_db),
                        limit: str = None,
                        skip: str = None):
    if limit is None:
        if request.cookies.get('limit') is None or request.cookies.get('skip_visualization') is None:
            limit = "5"
            skip = "0"
        else:
            limit = request.cookies.get('limit')
            skip = request.cookies.get('skip_visualization')
    elif not limit.isdigit() or int(limit) == 0:
        limit = "5"
    if not skip.isdigit():
        skip = "0"
    limit, skip = int(limit), int(skip)
    logger.info("Visualization page")
    count_todos = database.query(models.Todo).count() if type is None or not TodoTags.contains(
        type) else database.query(models.Todo).filter(
        models.Todo.type == type).count()
    count_pages = math.ceil(count_todos / limit)

    skip_todos = limit * skip
    if skip > count_pages:
        skip_todos = 0
    todos = database.query(models.Todo).order_by(models.Todo.id.desc()).filter(models.Todo.type == type).offset(
        skip_todos).limit(limit)
    if type is None or not TodoTags.contains(type):
        todos = database.query(models.Todo).order_by(models.Todo.id.desc()).offset(skip_todos).limit(limit)
    template_response = templates.TemplateResponse("visualization.html", {"request": request, "todos": todos,
                                                                          "limit": limit, "skip": skip,
                                                                          "count_pages": count_pages,
                                                                          "types": TodoTags})
    template_response.set_cookie("limit", value=str(limit))
    template_response.set_cookie("skip_visualization", value=str(skip))
    return template_response

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


@router.get("/visualize/{todo_id}", tags=["Files"])
async def visualisation_todo(request: Request, todo_id: int, database: Session = Depends(get_db)):
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()

    wc = WordCloud(width=300, height=300, background_color="white").generate(text=todo.details
    if todo.details is not None and todo.details.replace(" ", "") != ""
    else todo.title)
    plt.axis("off")
    plt.imshow(wc, interpolation="bilinear")

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    return Response(content=buffer.getvalue(),
                    media_type="image/png",
                    headers={"Content-Disposition": f"attachment; filename=Visualization{todo.id}.png"})


@router.get("/pageFile", tags=["Files"])
async def page_file(request: Request):
    return templates.TemplateResponse("pageFile.html", {"request": request})


@router.get("/generator", tags=["Generation"])
async def generator(request: Request):
    return templates.TemplateResponse("generator.html", {"request": request})


@router.get("/import_issues", tags=["Gitlab"])
async def issue_page(request: Request):
    return templates.TemplateResponse("import_issues.html", {"request": request})


def get_issues(url=Form(...),
               token=Form(...)):
    try:
        if "http" not in url:
            raise Exception
        proj = url.split("/")[-1]
        index = url.find("/", 9)
        plat = url[0:index]
        gl = gitlab.Gitlab(plat, token)
        gl.auth()
    except (GitlabAuthenticationError, Exception):
        raise HTTPException(status_code=status.HTTP_301_MOVED_PERMANENTLY)
    project = gl.projects.list(search=proj)
    issues = project[0].issues.list(get_all=True)
    issues.reverse()
    return issues


@router.post("/import_issues/", tags=["Gitlab"])
async def import_issues(
        request: Request,
        database: Session = Depends(get_db),
        current_user: models_login.Users = Depends(get_current_user),
        issues=Depends(get_issues)):
    for issue in issues:
        title = str(issue).split("title")[1].split("\'")[2]
        details = str(issue).split("description")[1].split("\'")[2]
        completed = str(issue).split("state")[1].split(",")[0].split("\'")[2]
        date_creation = datetime.datetime.strptime(str(issue).split("created_at")[1].split("\'")[2].split("T")[0],
                                                   "%Y-%m-%d").date()
        if completed == "closed":
            date_completion = datetime.datetime.strptime(
                (str(issue).split("closed_at")[1].split("\'")[2].split("T")[0]), "%Y-%m-%d").date()
        else:
            date_completion = None
        name = str(issue).split("username")[1].split("\'")[2]
        if name == "KLINTez":
            fullname = Users.user1.value
        elif name == "dedvkedahnike":
            fullname = Users.user2.value
        elif name == "kruasan":
            fullname = Users.user3.value
        else:
            fullname = Users.user1.value
        await todo_add(request=request,
                       title=title,
                       type=TodoTags.education.value,
                       source=Source.source_exported.value,
                       details=details,
                       date_creation=date_creation,
                       date_completion=date_completion,
                       completed=True if completed == "closed" else False,
                       fullname=fullname,
                       database=database,
                       current_user=current_user
                       )
    return {"answer": "ok"}


@router.get("/import_log/", tags=["Files"])
def import_log(request: Request, database: Session = Depends(get_db)):
    filenames = database.query(models.ImportedFiles).all()
    return templates.TemplateResponse("import_log.html", {"request": request, "filenames": filenames})


@router.post("/load_image/{todo_id}", status_code=status.HTTP_200_OK, tags=["Todo"])
def load_image(request: Request,
               todo_id: int,
               file_input: UploadFile = Form(),
               database: Session = Depends(get_db),
               current_user: models_login.Users = Depends(get_current_user)
               ):
    print("in func")
    if file_input.filename.split(".")[-1] != 'png':
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    todos_hashes = database.query(models.Todo).all()
    content = file_input.file.read()
    image = f"Image{todo.id}.png"
    path = str(Path.cwd() / "application" / "static" / "media" / image)
    buffer = io.BytesIO(content)

    image_for_hash = Image.open(buffer)
    hash = str(imagehash.average_hash(image_for_hash))
    for loaded_hash in todos_hashes:
        if loaded_hash.hash != "" and hash == loaded_hash.hash[0]:
            print(path)
            todo.image_path = loaded_hash.image_path
            todo.hash = loaded_hash.hash
            database.commit()
            return {"answer": "ok, copied"}

    try:
        with open(path, "wb") as f:
            f.write(buffer.getbuffer())
    except IsADirectoryError:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    todo.image_path = path
    todo.hash = str(hash)
    database.commit()
    return {"answer": "ok"}


@router.post("/load_txt/{todo_id}", status_code=status.HTTP_200_OK, tags=["Todo"])
def load_txt(request: Request,
             todo_id: int,
             file_input_txt: UploadFile = Form(),
             database: Session = Depends(get_db),
             current_user: models_login.Users = Depends(get_current_user)
             ):
    content = file_input_txt.file.read()
    es.editing_text_from_file_todo(todo_id, content.decode('utf-8'))
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if todo is not None:
        todo.text_from_file = content.decode('utf-8')
        todo.text_from_file_hash = hashlib.sha256(content).hexdigest()
        database.commit()
    return {"answer": "ok"}


@router.post("/generate/{todo_id}", tags=["Todo"])
async def vis(request: Request, todo_id: int, database: Session = Depends(get_db)):
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()

    wc = WordCloud(width=300, height=300, background_color="white").generate(text=todo.details
    if todo.details is not None and todo.details.replace(" ", "") != ""
    else todo.title)
    plt.axis("off")
    plt.imshow(wc, interpolation="bilinear")

    image = f"Image{todo.id}.png"
    path = str(Path.cwd() / "application" / "static" / "media" / image)
    plt.savefig(path, format='png')
    try:
        with open(path, "rb") as file:
            content = file.read()
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    buffer = io.BytesIO(content)

    image_for_hash = Image.open(buffer)
    hash = str(imagehash.average_hash(image_for_hash))
    todo.image_path = path
    todo.hash = hash
    database.commit()

    return {"answer": "ok"}


@router.post("/extend_detail/{todo_id}", tags=["Todo"])
async def extend_detail(request: Request,
                        todo_id: int,
                        database: Session = Depends(get_db),
                        current_user: models_login.Users = Depends(get_current_user)
                        ):
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=301)
    symbols = [".", ",", ";", ":", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "+", "=", "_", "`", "~", "<", ">",
               "?", "/", "\"", "\'", "\\", "|"]
    if todo.details is None or len(todo.details) <= 10:
        with open("application/todo/data/corpus.txt", encoding='utf-8') as f:
            text = f.read()
        text_model = markovify.Text(text)
        text_model.generate_corpus(text)
        todo.details = text_model.make_short_sentence(200)
    elif len(todo.details) > 10:
        words = todo.details.split(" ")
        last = words[-1]
        if last == "" or last in symbols:
            last = words[-2]
            lent = len(last)
            string = todo.details[0:(len(todo.details) - 2 - lent)]
        else:
            lent = len(last)
            string = todo.details[0:(len(todo.details) - 1 - lent)]
        if "." in last:
            last = last.split(".")[0]
        elif "!" in last:
            last = last.split("!")[0]
        elif "?" in last:
            last = last.split("?")[0]
        with open("application/todo/data/corpus.txt", encoding='utf-8') as f:
            text = f.read()
        text_model = markovify.Text(text)
        text_model.generate_corpus(text)
        count = 0
        while (count < 10):
            try:
                gen = text_model.make_short_sentence(200)
                strin = "\n" + last + " " + gen + "\n"
                for i in range(20):
                    new_text = text + strin
                new_model = markovify.Text(new_text)
                new_model.generate_corpus(new_text)
                tex = new_model.make_sentence_with_start(last)
                todo.details = string + " " + tex
                break
            except (ParamError, KeyError):
                count += 1
            if count == 10:
                text_model = markovify.Text(text)
                text_model.generate_corpus(text)
                todo.details = text_model.make_short_sentence(200)

    if len(todo.details) > 400:
        detail = todo.details[0:399]
        lenght = len(detail.split(" ")[-1])
        todo.details = todo.details[0:(398 - lenght)]

    database.commit()
    return {"answer": "ok"}


@router.get("/activity", response_class=HTMLResponse)
async def read_root(request: Request):
    users = await es.get_unique_users()
    return templates.TemplateResponse("activity.html", {"request": request, "users": users})


@router.post("/plot.png")
async def generate_plot(username: str = Form(...)):
    try:
        activity_data = await es.get_user_activity(username)

        if not activity_data["days"] or not activity_data["counts"]:
            raise ValueError("Нет данных для построения графика")
        dates = [datetime.datetime.strptime(day, "%Y-%m-%d") for day in activity_data["days"]]
        counts = activity_data["counts"]

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(dates, counts, marker='o', linestyle='-', color='tab:blue')
        ax.set_title(f'Активность пользователя {activity_data["username"]}')
        ax.set_xlabel('Дата')
        ax.set_ylabel('Количество записей')

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))  # Метки каждую неделю
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

        plt.xticks(rotation=45, ha='right')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)

        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, f"Ошибка: {str(e)}",
                ha='center', va='center', fontsize=12)
        ax.axis('off')

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

@router.get("/aggregation", response_class=HTMLResponse)
async def show_aggregation_form(request: Request, database: Session = Depends(get_db), date: Optional[str] = None, interval: Optional[str] = None):
    """Отображает форму агрегации или результаты"""
    if date and interval:
        # Показываем задачи для выбранного интервала
        ids = es.get_todos_for_interval(interval, date)
        todos = database.query(models.Todo).order_by(models.Todo.id.desc()).filter(models.Todo.id.in_(ids))
        return templates.TemplateResponse(
            "aggregation.html",
            {
                "request": request,
                "show_todos": True,
                "todos": todos,
                "selected_date": date,
                "interval_type": {
                    "1d": "день",
                    "1w": "неделя",
                    "1M": "месяц"
                }.get(interval, interval)
            }
        )
    else:
        # Показываем форму выбора интервала
        return templates.TemplateResponse(
            "aggregation.html",
            {
                "request": request,
                "show_todos": False
            }
        )

@router.post("/aggregation", response_class=HTMLResponse)
async def show_aggregation_results(
    request: Request,
    interval: str = Form(...)
):
    """Обрабатывает форму и показывает результаты агрегации"""
    aggregation_data = es.get_aggregation_data(interval)
    
    return templates.TemplateResponse(
        "aggregation.html",
        {
            "request": request,
            "show_todos": False,
            "interval_type": {
                "1d": "дни",
                "1w": "недели",
                "1M": "месяцы"
            }.get(interval, interval),
            "aggregation_data": aggregation_data,
            "raw_interval": interval
        }
    )

@router.get("/users_tags", response_class=HTMLResponse)
async def users_tags(request: Request,
                     database: Session = Depends(get_db)
                     ):
    return templates.TemplateResponse(
        "usersTags.html",
        {
            "request": request,
        }
    )

@router.post("/create_tag")
async def create_tag(request: Request,
                     tag_name: Annotated[str, Form()] = "",
                     database: Session = Depends(get_db),
                     current_user: models_login.Users = Depends(get_current_user)
                     ):
    if tag_name != "":
        tag = database.query(models.UsersTags).filter(models.UsersTags.tag == tag_name).count()
        if tag > 0:
            return {"answer": "tag exists"}
        database.add(
            models.UsersTags(tag=tag_name)   
        )
        database.commit()
        return {"answer": "ok"}
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


@router.delete("/delete_tag")
async def delete_tag(request: Request,
                     tag_name: Annotated[str, Form()] = "",
                     database: Session = Depends(get_db),
                     current_user: models_login.Users = Depends(get_current_user)
                     ):
    print(tag_name)
    if current_user.name != "admin":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if tag_name != "":
        tag = database.query(models.UsersTags).filter(models.UsersTags.tag == tag_name).all()
        print(tag)
        if len(tag) < 1:
            return {"answer": "tag  don`t exists"}
        for item in tag:
            database.delete(item)
        database.commit()
        return {"answer": "ok"}
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

@router.get("/get_tags")
async def get_tags(request: Request,
                   q: str = Query(..., min_length=1),
                   database: Session = Depends(get_db)
                   ):
    tags = (
        database.query(models.UsersTags.tag)
        .filter(models.UsersTags.tag.ilike(f"%{q}%"))
        .distinct()
        .limit(10)
        .all()
    )
    return [tag[0] for tag in tags if tag[0]]
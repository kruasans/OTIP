from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, Depends, status, Form, UploadFile, HTTPException
from starlette.responses import RedirectResponse, Response

from typing import Annotated
import io
import math
import os
import random
from datetime import date, datetime
import datetime
from loguru import logger
import gitlab
import pandas as pd
from gitlab import GitlabAuthenticationError
from matplotlib import pyplot as plt
from wordcloud import WordCloud
from PIL import Image
import imagehash

from application.database import get_db, Session
import application.todo.models as models
import application.login.models as models_login
from application.todo.tags import TodoTags, Users, Source, tags_metadata
from application.login.oauth2 import get_current_user

logger = logger.opt(colors=True)
# pylint: disable=invalid-name
templates = Jinja2Templates(directory="/application/templates")

router = APIRouter(
    prefix='/todo',
    tags=['Todo'],
)


@router.get("/list", tags=["Lists"])
async def list_todo(request: Request,
                    database: Session = Depends(get_db),
                    type: str = None,
                    limit: str = None,
                    skip: str = None):
    if limit is None:
        if request.cookies.get('limit') is None or not request.cookies.get('limit').isdigit():
            limit = "5"
        else:
            limit = request.cookies.get('limit')
    if skip is None:
        if request.cookies.get('skip') is None or not request.cookies.get('skip').isdigit():
            skip = "0"
        else:
            skip = request.cookies.get('skip')
    limit, skip = int(limit), int(skip)
    logger.info("Todo list")
    count_todos = database.query(models.Todo).count() if type is None or not TodoTags.contains(
        type) else database.query(models.Todo).filter(
        models.Todo.type == type).count()
    count_pages = math.ceil(count_todos / limit)

    skip_todos = limit * skip
    if skip > count_pages:
        skip_todos = skip = 0
    todos = database.query(models.Todo).order_by(models.Todo.id.desc()).filter(models.Todo.type == type).offset(
        skip_todos).limit(limit)
    if type is None or not TodoTags.contains(type):
        todos = database.query(models.Todo).order_by(models.Todo.id.desc()).offset(skip_todos).limit(limit)
    template_response = templates.TemplateResponse("list.html",
                                                   {
                                                       "request": request,
                                                       "todos": todos,
                                                       "limit": limit,
                                                       "skip": skip,
                                                       "count_pages": count_pages,
                                                       "types": TodoTags, "type": type})
    template_response.set_cookie("limit", str(limit))
    template_response.set_cookie("skip", str(skip))
    return template_response


@router.post("/add", tags=["Todo"])
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
                   current_user: models_login.Users = Depends(get_current_user)
                   ):
    """Add new todo
    """
    print("в /add")
    if title is not None and title.replace(" ", "") != "" or title == "":
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
        return {"answer": "ok"}
    return {"answer": "title not found"}


@router.get("/edit/{todo_id}", status_code=status.HTTP_200_OK, tags=["Todo"])
async def todo_get(request: Request,
                   todo_id: int,
                   database: Session = Depends(get_db)):
    """Get todo
    """
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    image = todo.image_path
    path = f"static/media/{image}"
    if not os.path.exists(path):
        todo.image_path = "Empty.png"
        image = "Empty.png"
    if todo is None:
        logger.info(f"Getting not existing todo: {todo}")
        return RedirectResponse(url=router.url_path_for("home"), status_code=status.HTTP_301_MOVED_PERMANENTLY)
    logger.info(f"Getting todo: {todo}")
    return templates.TemplateResponse("edit.html",
                                      {"request": request, "todo_id": todo_id, "todo": todo, "picture_name": image,
                                       "image": True, "fullnames": Users})


@router.post("/edit/{todo_id}", status_code=status.HTTP_200_OK, tags=["Todo"])
async def todo_edit(
        request: Request,
        todo_id: int,
        title: Annotated[str, Form(max_length=50)] = None,
        details: Annotated[str, Form(max_length=500)] = None,
        completed: bool = Form(False),
        fullname: Annotated[str, Form()] = "2021-3-26-cha",
        database: Session = Depends(get_db),
        current_user: models_login.Users = Depends(get_current_user)
):
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
        return {"answer": "ok"}
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    # return RedirectResponse(url=application.url_path_for("list_todo"), status_code=status.HTTP_303_SEE_OTHER)


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
        return RedirectResponse(url=router.url_path_for("home"), status_code=status.HTTP_301_MOVED_PERMANENTLY)
    logger.info(f"Deleting todo: {todo}")
    database.delete(todo)
    database.commit()
    return {"answer": "ok"}


@router.delete("/delete_all", tags=["Todo"])
async def todo_delete_all(request: Request,
                          database: Session = Depends(get_db),
                          current_user: models_login.Users = Depends(get_current_user)
                          ):
    """Delete all todos"""
    # Получаем все записи из базы данных
    all_todos = database.query(models.Todo).all()

    # Удаляем каждую запись
    for todo in all_todos:
        await todo_delete(request=request,
                          todo_id=todo.id,
                          database=database)

    return RedirectResponse(url=router.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)


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

    for i in range(0, count):
        title = titles[random.randint(0, 19)] + " " + titles[random.randint(0, 19)]
        type = types[random.randint(0, 2)]
        await todo_add(request=request,
                       title=title,
                       type=type,
                       source=Source.source_generated.value,
                       details=None,
                       database=database,
                       current_user=current_user
                       )
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
        # return RedirectResponse(url=application.url_path_for("page_file"), status_code=status.HTTP_301_MOVED_PERMANENTLY)
    content = file_input.file.read()
    buffer = io.BytesIO(content)
    df = pd.read_excel(buffer,
                       converters={'date_creation': pd.to_datetime,
                                   'date_completion': pd.to_datetime})
    print("перед /add")
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
                        limit: int = None,
                        skip: int = None):
    if limit is None:
        if request.cookies.get('limit') is None or request.cookies.get('skip_visualization') is None:
            limit = "5"
            skip = "0"
        else:
            limit = request.cookies.get('limit')
            skip = request.cookies.get('skip_visualization')
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
async def vis(request: Request, todo_id: int, database: Session = Depends(get_db)):
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


@router.post("/import_issues/", tags=["Gitlab"])
async def import_issues(
        request: Request,
        url: Annotated[str, Form()],
        token: Annotated[str, Form()],
        database: Session = Depends(get_db),
        current_user: models_login.Users = Depends(get_current_user)):
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
    print("find issues")
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
    if file_input.filename.split(".")[-1] != 'png':
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    todo = database.query(models.Todo).filter(models.Todo.id == todo_id).first()
    hashes = database.query(models.Todo.hash).all()
    content = file_input.file.read()
    image = f"Image{todo.id}.png"
    path = f"static/media/{image}"
    buffer = io.BytesIO(content)

    image_for_hash = Image.open(buffer)
    hash = str(imagehash.average_hash(image_for_hash))
    # print(f"Now loaded{hash}")
    for loaded_hash in hashes:
        print(f"loaded: {loaded_hash[0]}")
        if hash == loaded_hash[0]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

    try:
        with open(path, "wb") as f:
            f.write(buffer.getbuffer())
    except IsADirectoryError:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    todo.image_path = image
    todo.hash = str(hash)
    database.commit()
    return {"answer": "ok"}

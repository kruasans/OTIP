"""
Main of todo application
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request

from fastapi.templating import Jinja2Templates

from application.database import ENGINE, get_db

from application.todo import models as todo_models
from application.todo import routes as todo_routes
from application.todo import tags as todo_tags

from application.login import models as user_models
from application.login import routes as user_routes

from application.login.schems import UserCreate

todo_models.Base.metadata.create_all(bind=ENGINE)
user_models.Base.metadata.create_all(bind=ENGINE)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # allow_origins=['http://localhost:5500', 'http://127.0.0.1:5500', 'http://0.0.0.0:80'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/application/static", StaticFiles(directory="/application/static"), name="static")
app.mount("/application/media", StaticFiles(directory="/application/static"), name="static")

templates = Jinja2Templates(directory="/application/templates")


@app.get("/", status_code=status.HTTP_200_OK)
async def home(request: Request,
               database: Session = Depends(get_db),
               limit: str = None):
    """Main page with todo list"""
    if database.query(user_models.Users).filter(user_models.Users.name == "user").first() is None:
        await user_routes.create_user(UserCreate(username="user", password="user"), database)
    if limit is None:
        if request.cookies.get('limit') is None:
            limit = "5"
        else:
            limit = request.cookies.get('limit')
    count_cha = database.query(todo_models.Todo).filter(todo_models.Todo.fullname == "2021-3-26-cha").filter(
        todo_models.Todo.completed == True).count()
    count_zva = database.query(todo_models.Todo).filter(todo_models.Todo.fullname == "2021-3-04-zva").filter(
        todo_models.Todo.completed == True).count()
    count_pro = database.query(todo_models.Todo).filter(todo_models.Todo.fullname == "2021-3-12-pro").filter(
        todo_models.Todo.completed == True).count()
    template = templates.TemplateResponse("index.html",
                                          {"request": request, "types": todo_tags.TodoTags,
                                           "fullnames": todo_tags.Users, "cha": count_cha,
                                           "zva": count_zva, "pro": count_pro})
    template.set_cookie("limit", str(limit))
    return template


app.include_router(todo_routes.router)
app.include_router(user_routes.router)

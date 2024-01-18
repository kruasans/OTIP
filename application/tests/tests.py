import os

import pytest
import math

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from starlette import status

from application.database import get_db

from fastapi import FastAPI, Depends, HTTPException

from application.todo import models as todo_models
from application.todo import routes as todo_routes
from application.todo import tags as tags
from application.todo.routes import get_issues

from application.login import models as login_models
from application.login import routes as login_routes
from application.login.oauth2 import get_current_user
from application.todo.tags import TodoTags

t_app = FastAPI()

TEST_DB_URL = os.environ["DATABASE_URL"]
engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def override_get_current_user():
    return login_models.Users(id=1, name="user", password="user")


async def override_get_issues():
    data=[]
    with open("/application/tests/data/issue.txt", "r", encoding='utf-8') as file:
        data.append(file.read())
    return data


todo_models.Base.metadata.create_all(bind=engine)
login_models.Base.metadata.create_all(bind=engine)

t_app.include_router(todo_routes.router)
t_app.include_router(login_routes.router)

client = TestClient(t_app)

t_app.dependency_overrides[get_db] = override_get_db
t_app.dependency_overrides[get_current_user] = override_get_current_user
t_app.dependency_overrides[get_issues] = override_get_issues

@t_app.get("/test/todos")
async def get_todos(database: Session = Depends(get_db)):
    return database.query(todo_models.Todo).all()


@t_app.get("/test/import_files")
async def get_imported_files(database: Session = Depends(get_db)):
    return database.query(todo_models.ImportedFiles).all()


@t_app.post("/test/upload", status_code=200)
async def get_imported_files(filename: str = "file_name.xlsx", database: Session = Depends(get_db)):
    print(filename)
    if filename.split(".")[-1] != 'xlsx':
        raise HTTPException(status_code=status.HTTP_301_MOVED_PERMANENTLY)
    database.add(todo_models.ImportedFiles(file_name=filename))
    database.commit()
    return {"answer": "ok"}


@t_app.get("/tests/todo_list")
async def t_list_todo(
        limit: str = "5",
        skip: str = "0",
        type: str = None,
        database: Session = Depends(get_db)):
    limit, skip = int(limit), int(skip)
    count_todos = database.query(todo_models.Todo).count() if type is None or not TodoTags.contains(
        type) else database.query(todo_models.Todo).filter(
        todo_models.Todo.type == type).count()
    count_pages = math.ceil(count_todos / limit)

    skip_todos = limit * skip
    if skip > count_pages:
        skip_todos = skip = 0
    todos = database.query(todo_models.Todo).order_by(todo_models.Todo.id.desc()).filter(
        todo_models.Todo.type == type).offset(
        skip_todos).limit(limit)
    if type is None or not TodoTags.contains(type):
        todos = database.query(todo_models.Todo).order_by(todo_models.Todo.id.desc()).offset(skip_todos).limit(limit)
    todos = [todo for todo in todos]
    return todos



@pytest.mark.asyncio
class Test_class:
    @staticmethod
    async def test_remove_true():
        title = "text_title_to_delete"
        # добавляю тудушку
        client.post(
            "/todo/add",
            data={"title": title}
        )
        response = client.get(
            "/test/todos"
        )
        todos = response.json()
        id = 0
        for todo in todos:
            if todo["title"] == title:
                id = todo["id"]  # тут id добавленной тудушки

        # удаление по id
        response = client.delete(
            f"/todo/delete/{id}"
        )
        delete_response = response.json()  # сохраняю ответ

        response = client.get(
            "/test/todos"
        )
        todos = response.json()
        # ищу удалённую
        result = False
        for todo in todos:
            if todo["id"] == id:
                result = True

        assert result is False
        assert delete_response == {"answer": "ok"}

    @staticmethod
    async def test_remove_false():
        id = -1
        result_status = 301

        # удаление по несуществующему id
        response = client.delete(
            f"/todo/delete/{id}"
        )
        assert response.status_code == result_status

    @staticmethod
    async def test_import_log_true():
        filename = "test_file.xlsx"
        differance = 1

        response = client.get(
            "/test/import_files",
        )
        count_before = len(response.json())
        client.post(
            f"/test/upload?filename={filename}",
        )
        response = client.get(
            "/test/import_files",
        )
        count_after = len(response.json())

        assert count_after - count_before == differance

    @staticmethod
    async def test_import_log_wrong_file_format():
        filename = "test_file_wrong_format.csv"
        differance = 0

        response = client.get(
            "/test/import_files",
        )
        count_before = len(response.json())

        client.post(
            f"/test/upload?filename={filename}",
        )

        response = client.get(
            "/test/import_files",
        )
        count_after = len(response.json())

        assert count_after - count_before == differance


    # test ручки /add
    @staticmethod
    async def test_add_false():
        response = client.post(
            "/todo/add",
        )
        assert response.json() == {"answer": "title not found"}

    @staticmethod
    async def test_add_true():
        title = "text_title"
        response = client.post(
            "/todo/add",
            data={"title": title}
        )
        assert response.json() == {"answer": "ok"}
        response = client.get(
            "test/todos"
        )
        todos = response.json()
        for todo in todos:
            if todo["title"] == title:
                assert todo["title"] == title
                return
        return False

    @staticmethod
    async def test_todo_list():

        # Подготовка данных и выполнение тестов
        titles = ["text_title1", "text_title2", "text_title3", "text_title4", "text_title5"]

        # Вызов add для каждого title
        for title in titles:
            client.post(
                "/todo/add",
                data={"title": title}
            )

        response = client.get(
            "/test/todos",
        )
        todos = response.json()

        response = client.get(
            "/tests/todo_list?limit=5&skip=0"
        )
        result = response.json()

        expected = [todos[i] for i in range(len(todos) - 1, len(todos) - 6, -1)]
        assert result == expected

    @staticmethod
    async def test_todo_list():

        # Подготовка данных и выполнение тестов
        titles = ["text_title1", "text_title2", "text_title3", "text_title4", "text_title5"]

        # Вызов add для каждого title
        for title in titles:
            client.post(
                "/todo/add",
                data={"title": title}
            )

        response = client.get(
            "/test/todos",
        )
        todos = response.json()

        response = client.get(
            "/tests/todo_list?limit=5&skip=0"
        )
        result = response.json()

        expected = [todos[i] for i in range(len(todos) - 1, len(todos) - 6, -1)]
        assert result == expected

    @staticmethod
    async def test_todo_list_with_type():

        # Подготовка данных и выполнение тестов
        titles = ["text_title1", "text_title2", "text_title3", "text_title4", "text_title5"]

        # Вызов add для каждого title
        for title in titles:
            client.post(
                "/todo/add",
                data={"title": title,
                      "type": "Plan"}
            )

        response = client.get(
            "/test/todos",
        )
        todos = response.json()

        response = client.get(
            "/tests/todo_list?type=Plan&limit=5&skip=0"
        )
        result = response.json()

        expected = [todos[i] for i in range(len(todos) - 1, len(todos) - 6, -1)]
        assert result == expected

    @staticmethod
    async def test_todo_list_with_skip1():

        # Подготовка данных и выполнение тестов
        titles = ["text_title1", "text_title2", "text_title3", "text_title4", "text_title5"]

        # Вызов add для каждого title
        for title in titles:
            client.post(
                "/todo/add",
                data={"title": title}
            )

        response = client.get(
            "/test/todos",
        )
        todos = response.json()

        response = client.get(
            "/tests/todo_list?limit=5&skip=1"
        )
        result = response.json()

        expected = [todos[i] for i in range(len(todos) - 6, len(todos) - 11, -1)]
        assert result == expected

    @staticmethod
    async def test_import_issues():
        title="Visualaze delete all todo button"
        details=""
        completed=True
        type=tags.TodoTags.education.value
        source = tags.Source.source_exported.value
        fullname = tags.Users.user3.value
        response = client.post(
            "/todo/import_issues/",
        )
        import_responce = response.json()

        response = client.get(
            "/test/todos"
        )
        todos = response.json()
        result = False
        for todo in todos:
            if todo["title"]==title and todo["details"]==details and todo["completed"] == completed and todo["type"]==type and todo["source"]==source and todo["fullname"]==fullname:
                result = True
        assert result is True
        assert import_responce == {"answer": "ok"}

    @staticmethod
    async def test_edit_false():
        id = -1
        result_status = 301

        response = client.get(
            f"/todo/edit/{id}"
        )
        assert response.status_code == result_status

    @staticmethod
    async def test_edit():
        client.post(
            "/todo/add",
            data={"title": "Some text"}
        )
        response = client.get(
            "/test/todos"
        )
        todos = response.json()
        id = 0
        for todo in todos:
            if todo["title"] == "Some text":
                id = todo["id"]
        response_edit = client.post(
            f"/todo/edit/{id}",
            data={"title": "Another text", "completed": True}
        )
        response = client.get(
            "/test/todos"
        )
        todos = response.json()
        result = False
        for todo in todos:
            if todo["title"]=="Another text" and todo["completed"]==True and todo["image_path"]=="Empty.png":
                result = True
        assert result == True
        assert response_edit.status_code == 200


import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from starlette import status

from application.database import get_db

from fastapi import FastAPI, Depends, HTTPException

from application.todo import models as todo_models
from application.todo import routes as todo_routes

from application.login import models as login_models
from application.login import routes as login_routes
from application.login.oauth2 import get_current_user

t_app = FastAPI()

SQLALCHEMY_DATABASE_URL = "sqlite:///./application/tests/t_bd.sqlite"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def override_get_current_user():
    return login_models.Users(id=1, name="user", password="user")


todo_models.Base.metadata.create_all(bind=engine)
login_models.Base.metadata.create_all(bind=engine)

t_app.include_router(todo_routes.router)
t_app.include_router(login_routes.router)


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


client = TestClient(t_app)

t_app.dependency_overrides[get_db] = override_get_db
t_app.dependency_overrides[get_current_user] = override_get_current_user


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

        response = client.post(
            f"/test/upload?filename={filename}",
        )

        response = client.get(
            "/test/import_files",
        )
        count_after = len(response.json())

        assert count_after - count_before == differance

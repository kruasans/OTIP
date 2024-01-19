from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, Depends, status, Form, UploadFile, HTTPException

from loguru import logger

from application.database import get_db, Session
import application.login.models as models
from application.login import schems, oauth2
from application.login.hash_password import HashPassword

logger = logger.opt(colors=True)
# pylint: disable=invalid-name
templates = Jinja2Templates(directory="/application/templates")

router = APIRouter(
    prefix='/login',
    tags=["Login"],
)


@router.get('/log_in')
async def log_in(request: Request, database: Session = Depends(get_db)):
    if database.query(models.Users).filter(models.Users.name == "user").first() is None:
        await create_user(schems.UserCreate(username="user", password="user"), database)
    return templates.TemplateResponse("log_in.html", {"request": request})


@router.post('/token')
async def get_token(form_data: OAuth2PasswordRequestForm = Depends(), database: Session = Depends(get_db)):
    user = database.query(models.Users).filter(models.Users.name == form_data.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Invalid credentials')
    if not HashPassword.verify(user.password, form_data.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Wrong password')

    access_token = await oauth2.create_access_token(data={'username': user.name})
    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'user_id': user.id,
        'username': user.name
    }


async def create_user(form_data: schems.UserCreate, database: Session = Depends(get_db)):
    new_user = models.Users(name=form_data.username, password=HashPassword.bcrypt(form_data.password))
    database.add(new_user)
    database.commit()
    return new_user

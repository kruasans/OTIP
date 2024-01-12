from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

# from jose import jwt
# from jose.exceptions import JWTError

from passlib.context import CryptContext

from sqlalchemy.orm import Session
from starlette import status

from database import get_db
import models

password_context = CryptContext(schemes='bcrypt', deprecated='auto')

oauth2_schema = OAuth2PasswordBearer(tokenUrl='token')

SECRET_KEY = '52367badbf4e42f3a94d9ce456e1f01cbfee36a604da5c9589fa84f0bb9e661b'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30


async def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = to_encode["username"]
    # encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_schema), database: Session = Depends(get_db)):
    credentials_exeption = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authneticate': 'Bearer'}
    )

    try:
        payload = token
        # payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        decode_username: str = payload
        # decode_username: str = payload.get('username')

        if decode_username is None:
            raise credentials_exeption
    except HTTPException:
        raise credentials_exeption

    # TODO: check if token expires

    user = database.query(models.Users).filter(models.Users.name == decode_username).first()

    if user is None:
        raise credentials_exeption

    return user


class HashPassword:
    @staticmethod
    def verify(hashed_password, plain_password):
        return hashed_password == plain_password

from sqlalchemy import Column, Integer, Text

from application.database import Base


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    password = Column(Text)

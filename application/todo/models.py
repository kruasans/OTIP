from sqlalchemy import Column, Integer, Boolean, Text, Date, DateTime
from datetime import date, datetime
from pathlib import Path

from application.database import Base


class Todo(Base):
    """Todo model
    """
    __tablename__ = 'todos'
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    details = Column(Text, default="")
    completed = Column(Boolean, default=False)
    type = Column(Text)
    source = Column(Text)
    date_creation = Column(Date, default=date.today())
    date_completion = Column(Date, default=None)
    fullname = Column(Text, default="user")
    image_path = Column(Text, default= str(Path.cwd() / "application" / "static" / "media" / "Empty.png"))
    hash = Column(Text, default="")

    def __repr__(self):
        return f'<Todo {self.id}>'


class ImportedFiles(Base):
    __tablename__ = 'imported'
    id = Column(Integer, primary_key=True)
    file_name = Column(Text, default="")


class HistoryList(Base):
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True)
    todo_id = Column(Integer)
    date_event = Column(Date, default=date.today())
    time_event = Column(DateTime, default=datetime.now())
    event = Column(Text)
    fullname = Column(Text, default="user")

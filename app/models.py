"""Todo models
"""
from sqlalchemy import Column, Integer, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import date

from tags import TodoTags

Base = declarative_base()


class Todo(Base):
    """Todo model
    """
    __tablename__ = 'todos'
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    details = Column(Text)
    completed = Column(Boolean, default=False)
    type = Column(Text)
    date_creation = Column(Text, default=date.today())
    date_completion = Column(Text, default="-1")
    fullname = Column(Text, default="user")

    def __repr__(self):
        return f'<Todo {self.id}>'

"""Todo models
"""
from sqlalchemy import Column, Integer, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

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

    def __repr__(self):
        return f'<Todo {self.id}>'

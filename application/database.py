"""Database for todo
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session  # pylint: disable=unused-import

DB_URL = os.environ["DATABASE_URL"]
ENGINE = create_engine(os.environ["DATABASE_URL"])
SESSIONLOCAL = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)

Base = declarative_base()


def get_db():
    """Create session/connection for each request
    """
    database = SESSIONLOCAL()
    try:
        yield database
    finally:
        database.close()

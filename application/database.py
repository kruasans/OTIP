"""Database for todo
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session  # pylint: disable=unused-import

DB_URL = "sqlite:///./application/db.sqlite"
ENGINE = create_engine(DB_URL, connect_args={"check_same_thread": False})
# for logging all SQL-queries
# ENGINE = create_engine(DB_URL, connect_args={"check_same_thread": False}, echo=True)
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

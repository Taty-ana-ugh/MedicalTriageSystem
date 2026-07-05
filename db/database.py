"""
db/database.py
---------------
Engine + session setup. SQLite for now (zero external services needed to
run the project with one command, per Ray's Docker/one-command goal) --
swapping to Postgres later is a one-line DATABASE_URL change since
everything else goes through SQLAlchemy's engine-agnostic API.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./triage.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a session, always closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Idempotent -- safe to call more than once."""
    import db.models  # noqa: F401 -- ensures models are registered on Base before create_all
    Base.metadata.create_all(bind=engine)
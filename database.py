import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Railway injects DATABASE_URL automatically once Postgres is linked.
# Falls back to local SQLite when the variable isn't set (e.g. local dev).
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./wekasafe.db")

# Railway's URL starts with "postgresql://", but SQLAlchemy needs the
# psycopg2 driver spelled out explicitly.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# SQLite needs this connect_arg; Postgres does not (and will error if given it).
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

# Dependency for DB sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
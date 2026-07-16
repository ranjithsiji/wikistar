"""Database engine, session factory and the per-request session."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

from config import settings


class Base(DeclarativeBase):
    pass


# pool_recycle stays under ToolsDB's idle-connection kill window.
engine = create_engine(settings.database_url, pool_pre_ping=True,
                       pool_recycle=280)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# Request-scoped session; app.py removes it after every request.
db_session = scoped_session(SessionLocal)


def get_db():
    return db_session

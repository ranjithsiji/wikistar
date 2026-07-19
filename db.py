"""Database engine, session factory and the per-request session."""
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker
from sqlalchemy.schema import CreateColumn

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


def sync_schema() -> None:
    """Create missing tables, then add any mapped columns missing from
    existing tables. `create_all` only creates whole tables, so a new
    column on an existing model would otherwise 500 in production until an
    ALTER was run by hand. This backfill is additive and idempotent: it
    only ever ADDs columns present in the models but not in the database,
    never dropping or altering existing ones."""
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    compiler = engine.dialect.ddl_compiler(engine.dialect, None)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue  # just created with all columns by create_all
            have = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in have:
                    continue
                col_sql = compiler.process(CreateColumn(column))
                conn.exec_driver_sql(
                    f"ALTER TABLE {table.name} ADD COLUMN {col_sql}")

"""Drop and recreate the database schema from models.py.

DESTROYS ALL DATA in the database named by DATABASE_URL (environment
variable or config.toml).

Two modes:
    --tables-only   drop and recreate every table inside the existing
                    database. Use this on Toolforge: ToolsDB accounts may
                    not DROP/CREATE DATABASE, only their own tables.
    (default)       drop and recreate the whole database. Needs an account
                    with CREATE/DROP DATABASE rights (local dev).

Usage (from the project root):
    uv run python scripts/reset_db.py                    # local, asks to confirm
    uv run python scripts/reset_db.py --yes              # local, no prompt
    uv run python scripts/reset_db.py --tables-only      # Toolforge, asks to confirm
    uv run python scripts/reset_db.py --tables-only --yes
"""
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

# Run as a plain script (not `python -m`), so the project root — one
# level up from this file — needs to be on sys.path explicitly for the
# absolute `core.*` / `domain.*` imports below to resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import settings


def main() -> None:
    tables_only = "--tables-only" in sys.argv
    server_url, _, db_name = settings.database_url.rpartition("/")

    if "--yes" not in sys.argv:
        what = ("every table in" if tables_only else "the database")
        answer = input(f"Drop and recreate {what} '{db_name}'? "
                       f"ALL DATA WILL BE LOST. [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(1)

    from domain import models  # noqa: F401  (registers every table on Base.metadata)
    from core.db import Base, engine

    if tables_only:
        # Toolforge-safe: recreate tables inside the existing database.
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    else:
        # Connect with no default database selected: ToolsDB accounts have
        # no access to the `mysql` system schema, only to their own database.
        server = create_engine(f"{server_url}/")
        with server.begin() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS `{db_name}`"))
            conn.execute(
                text(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4"))
        server.dispose()
        print(f"Recreated database '{db_name}'.")
        Base.metadata.create_all(bind=engine)

    tables = ", ".join(sorted(Base.metadata.tables))
    print(f"Created tables: {tables}")


if __name__ == "__main__":
    main()

"""Drop the configured database and recreate it with a fresh schema.

DESTROYS ALL DATA in the database named by DATABASE_URL (environment
variable or config.toml), then recreates every table from models.py.

Usage:
    uv run python reset_db.py          # asks for confirmation
    uv run python reset_db.py --yes    # no prompt (scripts/CI)
"""
import sys

from sqlalchemy import create_engine, text

from config import settings


def main() -> None:
    server_url, _, db_name = settings.database_url.rpartition("/")

    if "--yes" not in sys.argv:
        answer = input(f"Drop database '{db_name}' and recreate it? "
                       f"ALL DATA WILL BE LOST. [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(1)

    # Connect with no default database selected: ToolsDB accounts have no
    # access to the `mysql` system schema, only to their own databases.
    server = create_engine(f"{server_url}/")
    with server.begin() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS `{db_name}`"))
        conn.execute(text(f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4"))
    server.dispose()
    print(f"Recreated database '{db_name}'.")

    import models  # noqa: F401  (registers every table on Base.metadata)
    from db import Base, engine

    Base.metadata.create_all(bind=engine)
    tables = ", ".join(sorted(Base.metadata.tables))
    print(f"Created tables: {tables}")


if __name__ == "__main__":
    main()

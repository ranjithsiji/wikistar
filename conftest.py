"""Test bootstrap: run the suite against a dedicated MariaDB test
database, never the configured dev/prod one.

Must set DATABASE_URL before any project module is imported, because
db.py creates the engine at import time. The server and credentials are
taken from the configured DATABASE_URL (env var or config.toml) with
the database name swapped to `wikistar_test`, which is created if
missing.
"""
import os
import tomllib
from pathlib import Path

TEST_DB_NAME = "wikistar_test"

_root = Path(__file__).resolve().parent
_url = os.environ.get("DATABASE_URL")
if not _url and (_root / "config.toml").exists():
    with open(_root / "config.toml", "rb") as f:
        _url = tomllib.load(f).get("DATABASE_URL")
if not _url:
    _url = "mysql+pymysql://root@localhost/wikistar"

_server, _, _ = _url.rpartition("/")
os.environ["DATABASE_URL"] = f"{_server}/{TEST_DB_NAME}"

from sqlalchemy import create_engine, text  # noqa: E402

_engine = create_engine(f"{_server}/mysql")
with _engine.begin() as conn:
    conn.execute(text(
        f"CREATE DATABASE IF NOT EXISTS {TEST_DB_NAME} CHARACTER SET utf8mb4"))
_engine.dispose()

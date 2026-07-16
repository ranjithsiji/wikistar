"""Test bootstrap: run the suite against a dedicated test database,
never the configured dev/prod one (the tests drop and recreate all
tables on every run).

Must set DATABASE_URL before any project module is imported, because
db.py creates the engine at import time. The test database reuses the
configured server and credentials with "_test" appended to the database
name — "wikistar" -> "wikistar_test" locally, "s56850__wikistar_p" ->
"s56850__wikistar_p_test" on ToolsDB (accounts may only create
databases under their own prefix). Created if missing.
"""
import os
import tomllib
from pathlib import Path

_root = Path(__file__).resolve().parent
_url = os.environ.get("DATABASE_URL")
if not _url and (_root / "config.toml").exists():
    with open(_root / "config.toml", "rb") as f:
        _url = tomllib.load(f).get("DATABASE_URL")
if not _url:
    _url = "mysql+pymysql://root@localhost/wikistar"

_server, _, _db_name = _url.rpartition("/")

# Tests are a development tool: refuse to run against production
# (ToolsDB) so a stray `pytest` on the server can never touch it.
if "tools.db.svc.wikimedia.cloud" in _server:
    raise SystemExit(
        "Refusing to run tests against ToolsDB (production). "
        "Run the test suite on a development machine with a local MariaDB.")

TEST_DB_NAME = f"{_db_name}_test"
os.environ["DATABASE_URL"] = f"{_server}/{TEST_DB_NAME}"

from sqlalchemy import create_engine, text  # noqa: E402

_engine = create_engine(f"{_server}/")
with _engine.begin() as conn:
    conn.execute(text(
        f"CREATE DATABASE IF NOT EXISTS `{TEST_DB_NAME}` CHARACTER SET utf8mb4"))
_engine.dispose()

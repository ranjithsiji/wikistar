"""Test bootstrap: run the whole app against a throwaway SQLite file.

Must set DATABASE_URL before any project module is imported, because
db.py creates the engine at import time.
"""
import os
import tempfile

_tmpdir = tempfile.mkdtemp(prefix="wikistar-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"

"""Application configuration.

Values are read from config.toml (sitting in the repo root, next to
pyproject.toml) and can be overridden by environment variables of the
same name.
"""
import os
import tomllib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT_DIR / "config.toml"

_DEFAULTS = {
    "SECRET_KEY": "dev-secret-change-me",
    "DATABASE_URL": f"sqlite:///{ROOT_DIR / 'instance' / 'dev.db'}",
    "CONSUMER_KEY": "",
    "CONSUMER_SECRET": "",
    "OAUTH_MWURI": "https://meta.wikimedia.org",
    "SESSION_COOKIE_SECURE": False,
    "FRONTEND_URL": "/",
}


def _load() -> dict:
    values = dict(_DEFAULTS)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            values.update(tomllib.load(f))
    for key in _DEFAULTS:
        if key in os.environ:
            raw = os.environ[key]
            if isinstance(_DEFAULTS[key], bool):
                values[key] = raw.lower() in ("1", "true", "yes")
            else:
                values[key] = raw
    return values


class Settings:
    def __init__(self) -> None:
        cfg = _load()
        self.secret_key: str = cfg["SECRET_KEY"]
        self.database_url: str = cfg["DATABASE_URL"]
        self.consumer_key: str = cfg["CONSUMER_KEY"]
        self.consumer_secret: str = cfg["CONSUMER_SECRET"]
        self.oauth_mwuri: str = cfg["OAUTH_MWURI"]
        self.session_cookie_secure: bool = bool(cfg["SESSION_COOKIE_SECURE"])
        self.frontend_url: str = cfg["FRONTEND_URL"]


settings = Settings()

"""Application configuration.

Values are read from config.toml (at the project root) and can be
overridden by environment variables of the same name.
"""
import os
import tomllib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT_DIR / "config.toml"

# The built-in fallback key: fine for local dev, unsafe in production
# because the whole session (and thus user identity) is signed with it.
DEV_SECRET_KEY = "dev-secret-change-me"

_DEFAULTS = {
    "SECRET_KEY": DEV_SECRET_KEY,
    "DATABASE_URL": "mysql+pymysql://root@localhost/wikistar",
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

        # Refuse to boot in production (signalled by the secure-cookie flag
        # the Toolforge deployment sets) with an unset or dev SECRET_KEY —
        # otherwise session cookies, which carry the user's identity, are
        # forgeable.
        if self.session_cookie_secure and self.secret_key in ("", DEV_SECRET_KEY):
            raise RuntimeError(
                "SECRET_KEY is unset or the built-in dev default while "
                "SESSION_COOKIE_SECURE is on. Set a strong, random SECRET_KEY "
                "in config.toml or the environment before deploying.")


settings = Settings()

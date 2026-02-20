import os
import tomllib

# Resolve the config.toml path relative to this file
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_BASE_DIR, 'config.toml')

# Load config.toml
with open(_CONFIG_PATH, 'rb') as _f:
    _cfg = tomllib.load(_f)


class Config:
    # Core
    SECRET_KEY = _cfg.get('SECRET_KEY', 'change-me')
    SQLALCHEMY_DATABASE_URI = _cfg.get('DATABASE_URL', 'sqlite:///fallback.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True

    # MediaWiki OAuth 2.0  (variable names match Toolforge conventions)
    CONSUMER_KEY    = _cfg.get('CONSUMER_KEY')
    CONSUMER_SECRET = _cfg.get('CONSUMER_SECRET')
    OAUTH_MWURI     = _cfg.get('OAUTH_MWURI', 'https://meta.wikimedia.org')

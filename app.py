"""WikiSTAR v2 application entry point (Flask).

Run locally:   uv run python app.py   (or: uv run flask --app app run --debug)

Toolforge (classic python webservice): clone the repo to
~/www/python/src and install requirements.txt into ~/www/python/venv;
uwsgi serves the `app` callable below directly.
"""
from flask import Flask, send_file
from werkzeug.middleware.proxy_fix import ProxyFix

from auth import oauth
from config import ROOT_DIR, settings
from db import Base, db_session, engine, sync_schema
from routers import (admin, auth as auth_routes, campaigns, claims, dashboard,
                     reviews, submissions)
from webutil import register_errors

app = Flask(__name__)
app.secret_key = settings.secret_key
app.config.update(
    SESSION_COOKIE_SECURE=settings.session_cookie_secure,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
# Trust the Toolforge front proxy so url_for(_external=True) builds
# https://wikistar.toolforge.org/... URLs (needed for the OAuth callback).
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

oauth.init_app(app)
register_errors(app)

for module in (auth_routes, campaigns, submissions, reviews, claims, admin,
               dashboard):
    app.register_blueprint(module.bp)

# Create missing tables and additively backfill any new mapped columns,
# so deploying a model change never 500s on an un-migrated column.
sync_schema()
# uwsgi imports the app in the master and then forks workers: drop the
# connection the line above pooled, so workers never share one socket.
engine.dispose()


@app.teardown_appcontext
def _remove_db_session(exc):
    db_session.remove()


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


# ---- serve the built SPA ---------------------------------------------------
DIST = ROOT_DIR / "frontend" / "dist"
if DIST.exists():
    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def spa(path: str):
        candidate = (DIST / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(DIST):
            return send_file(candidate)
        return send_file(DIST / "index.html")


# Alternate WSGI entry point name, in case uwsgi is configured with
# `callable = application`.
application = app

if __name__ == "__main__":
    app.run(debug=True, port=8000)

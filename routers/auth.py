"""Login / logout / current user."""
from flask import Blueprint, redirect, session, url_for

from auth import fetch_profile, get_current_user, oauth, upsert_user
from config import settings
from db import get_db

bp = Blueprint("auth", __name__)


@bp.get("/api/login")
def login():
    redirect_uri = url_for("auth.oauth_callback", _external=True)
    if settings.session_cookie_secure:
        redirect_uri = redirect_uri.replace("http://", "https://", 1)
    return oauth.mediawiki.authorize_redirect(redirect_uri)


@bp.get("/oauth-callback")
def oauth_callback():
    profile = fetch_profile()
    user = upsert_user(get_db(), profile)
    session["user_id"] = user.id
    return redirect(settings.frontend_url)


@bp.get("/api/logout")
def logout():
    session.pop("user_id", None)
    return redirect(settings.frontend_url)


@bp.get("/api/me")
def me():
    user = get_current_user()
    if user is None:
        return {"user": None}
    return {"user": {"id": user.id, "username": user.username,
                     "is_admin": user.is_admin}}

"""Login / logout / current user."""
from flask import Blueprint, redirect, request, session, url_for

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


def _login_notice(reason: str):
    return redirect(f"{settings.frontend_url}?login={reason}")


@bp.get("/oauth-callback")
def oauth_callback():
    # The user may reject the request on meta — Wikimedia then calls back
    # with error=... and no code. Bounce home with a notice, never a 500.
    if request.args.get("error") or not request.args.get("code"):
        return _login_notice("cancelled")
    try:
        profile = fetch_profile()
    except Exception:
        # Expired/forged state, network trouble with meta, … — anything
        # that breaks the token exchange lands here.
        return _login_notice("failed")
    user = upsert_user(get_db(), profile)
    session["user_id"] = user.id
    return redirect(settings.frontend_url)


@bp.get("/api/logout")
def logout():
    session.pop("user_id", None)
    session.pop("oauth_token", None)
    return redirect(settings.frontend_url)


@bp.get("/api/me")
def me():
    user = get_current_user()
    if user is None:
        return {"user": None}
    return {"user": {"id": user.id, "username": user.username,
                     "is_admin": user.is_admin}}

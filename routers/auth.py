"""Login / logout / current user."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import fetch_profile, get_current_user, oauth, upsert_user
from config import settings
from db import get_db
from models import User

router = APIRouter(tags=["auth"])


@router.get("/api/login")
async def login(request: Request):
    redirect_uri = str(request.url_for("oauth_callback"))
    if settings.session_cookie_secure:
        redirect_uri = redirect_uri.replace("http://", "https://", 1)
    return await oauth.mediawiki.authorize_redirect(request, redirect_uri)


@router.get("/oauth-callback", name="oauth_callback")
async def oauth_callback(request: Request, db: Session = Depends(get_db)):
    profile = await fetch_profile(request)
    user = upsert_user(db, profile)
    request.session["user_id"] = user.id
    return RedirectResponse(settings.frontend_url)


@router.get("/api/logout")
async def logout(request: Request):
    request.session.pop("user_id", None)
    return RedirectResponse(settings.frontend_url)


@router.get("/api/me")
def me(user: User | None = Depends(get_current_user)):
    if user is None:
        return {"user": None}
    return {"user": {"id": user.id, "username": user.username,
                     "is_admin": user.is_admin}}

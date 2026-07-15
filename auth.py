"""MediaWiki OAuth 2.0 (Authlib Starlette client) + auth dependencies.

Flow (identical to the proven Flask v1 flow, ported to FastAPI):
  GET /api/login      -> authorize_redirect to {OAUTH_MWURI}/w/rest.php/oauth2/authorize
  GET /oauth-callback -> authorize_access_token, then GET oauth2/resource/profile
                         -> upsert User, store user_id in the signed session cookie

Identity for every API call comes ONLY from the session cookie — the
client never sends usernames.
"""
from datetime import datetime, timezone

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from config import settings
from db import get_db
from models import Campaign, CampaignMember, MemberRole, User

USER_AGENT = "WikiSTAR/2.0 (https://wikistar.toolforge.org)"

oauth = OAuth()
oauth.register(
    name="mediawiki",
    client_id=settings.consumer_key,
    client_secret=settings.consumer_secret,
    authorize_url=f"{settings.oauth_mwuri}/w/rest.php/oauth2/authorize",
    access_token_url=f"{settings.oauth_mwuri}/w/rest.php/oauth2/access_token",
    api_base_url=f"{settings.oauth_mwuri}/w/rest.php/",
    client_kwargs={"headers": {"User-Agent": USER_AGENT}},
)


async def fetch_profile(request: Request) -> dict:
    """Exchange the callback code for a token and fetch the user profile."""
    token = await oauth.mediawiki.authorize_access_token(request)
    resp = await oauth.mediawiki.get("oauth2/resource/profile", token=token)
    resp.raise_for_status()
    return resp.json()


def upsert_user(db: Session, profile: dict) -> User:
    """Create or update the local user record from the OAuth profile."""
    username = profile.get("username")
    if not username:
        raise HTTPException(502, "MediaWiki profile did not include a username")
    global_id = profile.get("sub")
    user = None
    if global_id is not None:
        user = db.query(User).filter_by(mw_global_id=int(global_id)).first()
    if user is None:
        user = db.query(User).filter_by(username=username).first()
    if user is None:
        user = User(username=username)
        db.add(user)
    user.username = username  # follows renames when matched by global id
    if global_id is not None:
        user.mw_global_id = int(global_id)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return user


# ---- dependencies ----------------------------------------------------------

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return db.get(User, user_id)


def require_user(user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(401, "Login required")
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, "Admin access required")
    return user


def campaign_roles(db: Session, campaign: Campaign, user: User | None) -> set[MemberRole]:
    if user is None:
        return set()
    rows = (
        db.query(CampaignMember.role)
        .filter_by(campaign_id=campaign.id, user_id=user.id)
        .all()
    )
    return {r[0] for r in rows}


def require_organizer(db: Session, campaign: Campaign, user: User) -> None:
    """Organizer of this campaign, or site admin."""
    if user.is_admin or MemberRole.organizer in campaign_roles(db, campaign, user):
        return
    raise HTTPException(403, "Organizer access required")


def require_jury(db: Session, campaign: Campaign, user: User) -> None:
    """Jury member of this campaign, organizer, or site admin."""
    roles = campaign_roles(db, campaign, user)
    if user.is_admin or roles & {MemberRole.jury, MemberRole.organizer}:
        return
    raise HTTPException(403, "Jury access required")

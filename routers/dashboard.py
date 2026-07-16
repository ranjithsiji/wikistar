"""Personal dashboard ("Personal Cabinet"), modelled on Fountain.

Four sections, all scoped to the logged-in user:
  participation  campaigns you submitted to, with a leaderboard window
                 around your rank (hidden when the campaign hides marks)
  evaluation     campaigns where you are on the jury, with the number of
                 submissions still waiting for your review
  created        campaigns you created (drafts included)
  approval       draft campaigns you hold the right to approve
"""
import re

from flask import Blueprint, request
from sqlalchemy.orm import selectinload

import wiki_rights
from auth import campaign_roles, require_user
from db import get_db
from models import (
    Campaign,
    CampaignMember,
    CampaignStatus,
    MemberRole,
    ScoringMode,
    Submission,
)
from routers.common import campaign_summary, compute_leaderboard
from webutil import HTTPException, jsonable, respond

bp = Blueprint("dashboard", __name__, url_prefix="/api/me")

_LANG_RE = re.compile(r"^[a-z][a-z0-9-]{1,11}$")


@bp.get("/preferences")
def get_preferences():
    user = require_user()
    langs = [code for code in (user.preferred_languages or "").split(",") if code]
    return respond({"preferred_languages": langs})


@bp.put("/preferences")
def save_preferences():
    db, user = get_db(), require_user()
    data = request.get_json(silent=True) or {}
    langs = data.get("preferred_languages") or []
    if not isinstance(langs, list) or len(langs) > 10:
        raise HTTPException(
            400, "preferred_languages must be a list of up to 10 codes")
    clean: list[str] = []
    for lang in langs:
        code = str(lang).strip().lower()
        if not _LANG_RE.match(code):
            raise HTTPException(400, f"Invalid language code: {lang}")
        if code not in clean:
            clean.append(code)
    user.preferred_languages = ",".join(clean)
    db.commit()
    return respond({"preferred_languages": clean})


def _summary(campaign: Campaign) -> dict:
    return jsonable(campaign_summary(campaign))


@bp.get("/participation")
def participation():
    db, user = get_db(), require_user()
    campaigns = (
        db.query(Campaign)
        .join(Submission, Submission.campaign_id == Campaign.id)
        .filter(Submission.user_id == user.id)
        .distinct()
        .order_by(Campaign.end_date.desc())
        .all()
    )
    out = []
    for c in campaigns:
        # Fountain's HiddenMarks: in anonymous jury campaigns only
        # organizers/admins see the standings.
        hidden = (bool(c.effective_settings.get("anonymous_reviews"))
                  and c.scoring_mode == ScoringMode.jury
                  and not (user.is_admin or MemberRole.organizer
                           in campaign_roles(db, c, user)))
        rows = []
        if not hidden:
            board = compute_leaderboard(db, c)
            me = next((r for r in board if r.user.id == user.id), None)
            if me is not None:
                rows = [
                    {"rank": r.rank, "username": r.user.username,
                     "points": r.points, "me": r.user.id == user.id}
                    for r in board
                    if me.rank - 1 <= r.rank <= me.rank + 1
                ]
        out.append({**_summary(c), "hidden_marks": hidden, "rows": rows})
    return respond(out)


@bp.get("/evaluation")
def evaluation():
    db, user = get_db(), require_user()
    campaigns = (
        db.query(Campaign)
        .join(CampaignMember, CampaignMember.campaign_id == Campaign.id)
        .filter(CampaignMember.user_id == user.id,
                CampaignMember.role == MemberRole.jury)
        .order_by(Campaign.end_date.desc())
        .all()
    )
    out = []
    for c in campaigns:
        subs = (db.query(Submission)
                .filter_by(campaign_id=c.id)
                .options(selectinload(Submission.reviews))
                .all())
        missing = sum(
            1 for s in subs
            if s.user_id != user.id
            and all(r.reviewer_id != user.id for r in s.reviews)
        )
        out.append({**_summary(c), "missing": missing})
    return respond(out)


@bp.get("/created")
def created():
    db, user = get_db(), require_user()
    campaigns = (db.query(Campaign)
                 .filter_by(created_by=user.id)
                 .order_by(Campaign.start_date.desc())
                 .all())
    return respond([_summary(c) for c in campaigns])


@bp.get("/approval")
def approval():
    db, user = get_db(), require_user()
    drafts = (db.query(Campaign)
              .filter(Campaign.status == CampaignStatus.draft)
              .order_by(Campaign.start_date.desc())
              .all())
    return respond([_summary(c) for c in drafts
                    if wiki_rights.can_approve_campaign(user, c)[0]])

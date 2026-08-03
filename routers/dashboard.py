"""Personal dashboard ("Personal Cabinet"), modelled on Fountain.

Five sections, all scoped to the logged-in user:
  participation  campaigns you submitted to, with a leaderboard window
                 around your rank (hidden when the campaign hides marks)
  submissions    every submission you've made, across every campaign,
                 with a withdraw action (own submission, active campaign)
  evaluation     campaigns where you are on the jury, with the number of
                 submissions still waiting for your review
  created        campaigns you created (drafts included)
  approval       draft campaigns you hold the right to approve
"""
import re

from flask import Blueprint, request
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from integrations import wiki_rights
from auth import campaign_roles, require_user
from core.db import get_db
from core.webutil import HTTPException, jsonable, respond
from domain.models import (
    Campaign,
    CampaignMember,
    CampaignStatus,
    MemberRole,
    Review,
    ScoringMode,
    Submission,
)
from routers.common import (campaign_counts, campaign_summary,
                            compute_leaderboard, submission_out)

bp = Blueprint("dashboard", __name__, url_prefix="/api/me")

_LANG_RE = re.compile(r"^[a-z][a-z0-9-]{1,11}$")


def _clean_codes(value, field: str) -> list[str]:
    """Validate a list of wiki language codes (max 10, deduplicated)."""
    if not isinstance(value, list) or len(value) > 10:
        raise HTTPException(400, f"{field} must be a list of up to 10 codes")
    clean: list[str] = []
    for lang in value:
        code = str(lang).strip().lower()
        if not _LANG_RE.match(code):
            raise HTTPException(400, f"Invalid language code: {lang}")
        if code not in clean:
            clean.append(code)
    return clean


@bp.get("/preferences")
def get_preferences():
    user = require_user()
    langs = [code for code in (user.preferred_languages or "").split(",") if code]
    wikis = [code for code in (user.home_wikis or "").split(",") if code]
    return respond({"preferred_languages": langs, "home_wikis": wikis})


@bp.put("/preferences")
def save_preferences():
    db, user = get_db(), require_user()
    data = request.get_json(silent=True) or {}
    langs = _clean_codes(data.get("preferred_languages") or [],
                         "preferred_languages")
    wikis = _clean_codes(data.get("home_wikis") or [], "home_wikis")
    user.preferred_languages = ",".join(langs)
    user.home_wikis = ",".join(wikis)
    db.commit()
    return respond({"preferred_languages": langs, "home_wikis": wikis})


def _summary(db, campaign: Campaign, counts: dict | None = None) -> dict:
    return jsonable(campaign_summary(db, campaign, counts))


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
    counts = campaign_counts(db, campaigns)
    out = []
    for c in campaigns:
        # Fountain's HiddenMarks: in anonymous jury campaigns only
        # organizers/admins see the standings.
        hidden = (bool(c.effective_settings.get("anonymous_reviews"))
                  and c.scoring_mode == ScoringMode.jury
                  and not (user.is_admin or MemberRole.organizer
                           in campaign_roles(db, c, user)))
        rows = []
        mine = None
        if not hidden:
            board = compute_leaderboard(db, c)
            me = next((r for r in board if r.user.id == user.id), None)
            if me is not None:
                mine = {"submission_count": me.submission_count,
                        "bytes_added": me.bytes_added, "points": me.points}
                rows = [
                    {"rank": r.rank, "username": r.user.username,
                     "points": r.points, "me": r.user.id == user.id}
                    for r in board
                    if me.rank - 1 <= r.rank <= me.rank + 1
                ]
        out.append({**_summary(db, c, counts[c.id]), "hidden_marks": hidden,
                    "rows": rows, "mine": mine})
    return respond(out)


@bp.get("/submissions")
def my_submissions():
    """Every submission the user has made, newest first, across every
    campaign — each with its campaign's slug/name/status so the frontend
    can link back and gate withdrawal (own submission, campaign active)."""
    db, user = get_db(), require_user()
    subs = (
        db.query(Submission)
        .filter_by(user_id=user.id)
        .options(
            selectinload(Submission.reviews),
            selectinload(Submission.claims),
            selectinload(Submission.campaign),
        )
        .order_by(Submission.submitted_at.desc())
        .all()
    )
    out = []
    for s in subs:
        campaign = s.campaign
        item = jsonable(submission_out(campaign, s))
        item["campaign"] = {"slug": campaign.slug, "name": campaign.name,
                            "status": campaign.status.value}
        out.append(item)
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
    counts = campaign_counts(db, campaigns)
    out = []
    for c in campaigns:
        missing = (
            db.query(func.count(Submission.id))
            .filter(Submission.campaign_id == c.id,
                    Submission.user_id != user.id,
                    ~Submission.reviews.any(Review.reviewer_id == user.id))
            .scalar()
        )
        out.append({**_summary(db, c, counts[c.id]), "missing": missing})
    return respond(out)


@bp.get("/created")
def created():
    db, user = get_db(), require_user()
    campaigns = (db.query(Campaign)
                 .filter_by(created_by=user.id)
                 .order_by(Campaign.start_date.desc())
                 .all())
    counts = campaign_counts(db, campaigns)
    return respond([_summary(db, c, counts[c.id]) for c in campaigns])


@bp.get("/approval")
def approval():
    db, user = get_db(), require_user()
    drafts = (db.query(Campaign)
              .filter(Campaign.status == CampaignStatus.draft)
              .order_by(Campaign.start_date.desc())
              .all())
    # can_approve_campaign resolves the user's on-wiki rights through a
    # process-wide cache, so the whole list costs one API call at worst.
    visible = [c for c in drafts
               if wiki_rights.can_approve_campaign(user, c)[0]]
    counts = campaign_counts(db, visible)
    return respond([_summary(db, c, counts[c.id]) for c in visible])

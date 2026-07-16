"""Submissions: participants add their contributions to a campaign.

Identity always comes from the session. Submitting auto-joins the
campaign as participant (same flow in jury and self modes). Page
metadata is fetched from the MediaWiki API at submission time and can
be refreshed; a failed fetch never blocks the submission.
"""
from datetime import date, datetime, timezone

from flask import Blueprint
from sqlalchemy.orm import Session

import mediawiki
from auth import (
    campaign_roles,
    get_current_user,
    require_organizer,
    require_user,
)
from db import get_db
from models import (
    Campaign,
    CampaignMember,
    CampaignStatus,
    MemberRole,
    ScoringMode,
    Submission,
    SubmissionKind,
    User,
)
from routers.common import (
    audit,
    get_campaign_or_404,
    load_submissions,
    submission_out,
)
from schemas import SubmissionIn, SubmissionModerationIn
from webutil import HTTPException, parse, respond

bp = Blueprint("submissions", __name__, url_prefix="/api")

WIKIDATA_DOMAIN = "www.wikidata.org"


def _get_submission_or_404(db: Session, submission_id: int) -> Submission:
    sub = db.get(Submission, submission_id)
    if sub is None:
        raise HTTPException(404, "Submission not found")
    return sub


def _fetch_metadata(sub: Submission, campaign: Campaign,
                    username: str) -> "mediawiki.PageMetadata | None":
    """Best-effort MediaWiki metadata snapshot."""
    try:
        meta = mediawiki.fetch_page_metadata(
            sub.wiki_domain, sub.title, username,
            campaign.start_date, campaign.end_date)
    except Exception:
        return None
    if not meta.exists:
        return meta
    sub.page_id = meta.page_id
    sub.page_len = meta.page_len
    sub.current_rev_id = meta.current_rev_id
    sub.base_rev_id = meta.base_rev_id
    sub.bytes_added = meta.bytes_added
    sub.is_new_page = meta.is_new_page
    sub.metadata_fetched_at = datetime.now(timezone.utc)
    return meta


def _check_eligibility(sub: Submission, campaign: Campaign, user: User,
                       settings: dict,
                       meta: "mediawiki.PageMetadata | None") -> None:
    """Fountain-style eligibility rules, checked against fetched metadata.
    Checks that need metadata are skipped when the fetch failed — the
    organizer can still reject after a manual refresh."""
    if sub.metadata_fetched_at is not None:
        if (settings.get("require_page_created_during_campaign")
                and not sub.is_new_page):
            raise HTTPException(
                400, "Only pages created during the campaign are accepted")
        min_bytes = int(settings.get("min_article_bytes", 0) or 0)
        if min_bytes and (sub.page_len or 0) < min_bytes:
            raise HTTPException(
                400, f"The page is smaller than {min_bytes} bytes")
        if (settings.get("submitter_must_be_creator")
                and meta is not None and meta.creator
                and meta.creator != user.username):
            raise HTTPException(
                400, "Only the creator of the page may submit it")
    registered_after = settings.get("submitter_registered_after") or ""
    if registered_after:
        try:
            cutoff = date.fromisoformat(registered_after)
        except ValueError:
            return
        try:
            registration = mediawiki.fetch_user_registration(
                sub.wiki_domain, user.username)
        except Exception:
            return
        if registration is not None and registration.date() < cutoff:
            raise HTTPException(
                400, "This campaign is only open to accounts created "
                     f"after {registered_after}")


@bp.get("/campaigns/<slug>/submissions")
def list_submissions(slug: str):
    db, user = get_db(), get_current_user()
    campaign = get_campaign_or_404(db, slug)
    settings = campaign.effective_settings
    out = [submission_out(campaign, s, settings)
           for s in load_submissions(db, campaign.id)]

    # Fountain's HiddenMarks: only organizers/admins see marks and points;
    # jurors additionally see their own review.
    if settings.get("anonymous_reviews"):
        privileged = user is not None and (
            user.is_admin
            or MemberRole.organizer in campaign_roles(db, campaign, user))
        if not privileged:
            for item in out:
                item.reviews = [r for r in item.reviews
                                if user and r.reviewer.id == user.id]
                if campaign.scoring_mode == ScoringMode.jury:
                    item.points = 0
                    item.breakdown = []
    return respond(out)


@bp.post("/campaigns/<slug>/submissions")
def create_submission(slug: str):
    db, user = get_db(), require_user()
    payload = parse(SubmissionIn)
    campaign = get_campaign_or_404(db, slug)
    settings = campaign.effective_settings

    if campaign.status != CampaignStatus.active:
        raise HTTPException(400, "This campaign does not accept submissions")
    if (date.today() > campaign.end_date
            and not settings.get("allow_submissions_after_end")):
        raise HTTPException(400, "The campaign has ended")
    if (payload.kind == SubmissionKind.article
            and not settings.get("allow_articles", True)):
        raise HTTPException(400, "This campaign does not accept articles")
    if (payload.kind == SubmissionKind.wikidata_item
            and not settings.get("allow_wikidata_items")):
        raise HTTPException(400,
                            "This campaign does not accept Wikidata items")

    roles = campaign_roles(db, campaign, user)
    if MemberRole.jury in roles and not settings.get("jury_can_submit"):
        raise HTTPException(403, "Jury members cannot submit to this campaign")

    title = payload.title.strip()
    existing = db.query(Submission).filter_by(
        campaign_id=campaign.id, user_id=user.id, title=title).first()
    if existing:
        raise HTTPException(409, "You already submitted this page")

    max_subs = int(settings.get("max_submissions_per_user", 0) or 0)
    if max_subs:
        count = db.query(Submission).filter_by(
            campaign_id=campaign.id, user_id=user.id).count()
        if count >= max_subs:
            raise HTTPException(
                400, f"Submission limit of {max_subs} reached")

    sub = Submission(
        campaign_id=campaign.id, user_id=user.id, kind=payload.kind,
        title=title,
        wiki_domain=(WIKIDATA_DOMAIN
                     if payload.kind == SubmissionKind.wikidata_item
                     else campaign.wiki_domain),
    )
    meta = _fetch_metadata(sub, campaign, user.username)
    _check_eligibility(sub, campaign, user, settings, meta)
    db.add(sub)

    if MemberRole.participant not in roles:
        db.add(CampaignMember(campaign_id=campaign.id, user_id=user.id,
                              role=MemberRole.participant, added_by=user.id))
    audit(db, user, "submit", "submission", None,
          {"campaign": slug, "title": title})
    db.commit()
    db.refresh(sub)
    return respond(submission_out(campaign, sub, settings), 201)


@bp.delete("/submissions/<int:submission_id>")
def delete_submission(submission_id: int):
    db, user = get_db(), require_user()
    sub = _get_submission_or_404(db, submission_id)
    campaign = sub.campaign
    if sub.user_id != user.id:
        require_organizer(db, campaign, user)
    elif campaign.status != CampaignStatus.active:
        raise HTTPException(
            403, "Own submissions can only be withdrawn while the campaign runs")
    audit(db, user, "withdraw", "submission", sub.id,
          {"campaign": campaign.slug, "title": sub.title})
    db.delete(sub)
    db.commit()
    return respond(None, 204)


@bp.post("/submissions/<int:submission_id>/refresh")
def refresh_metadata(submission_id: int):
    db, user = get_db(), require_user()
    sub = _get_submission_or_404(db, submission_id)
    campaign = sub.campaign
    if sub.user_id != user.id:
        require_organizer(db, campaign, user)
    _fetch_metadata(sub, campaign, sub.user.username)
    db.commit()
    db.refresh(sub)
    return respond(submission_out(campaign, sub))


@bp.post("/submissions/<int:submission_id>/moderate")
def moderate_submission(submission_id: int):
    """Organizer final say: accept/reject and points override."""
    db, user = get_db(), require_user()
    payload = parse(SubmissionModerationIn)
    sub = _get_submission_or_404(db, submission_id)
    campaign = sub.campaign
    require_organizer(db, campaign, user)
    if payload.status is not None:
        sub.status = payload.status
    if payload.clear_override:
        sub.points_override = None
    elif payload.points_override is not None:
        sub.points_override = payload.points_override
    audit(db, user, "moderate", "submission", sub.id,
          {"campaign": campaign.slug, "title": sub.title,
           "status": sub.status.value,
           "points_override": (float(sub.points_override)
                               if sub.points_override is not None else None)})
    db.commit()
    db.refresh(sub)
    return respond(submission_out(campaign, sub))

"""Submissions: participants add their contributions to a campaign.

Identity always comes from the session. Submitting auto-joins the
campaign as participant (same flow in jury and self modes). Page
metadata is fetched from the MediaWiki API at submission time and can
be refreshed; a failed fetch never blocks the submission.
"""
from datetime import date, datetime, timezone

from flask import Blueprint
from sqlalchemy.orm import Session

from integrations import mediawiki
from auth import (
    campaign_roles,
    get_current_user,
    get_session_oauth_token,
    require_organizer,
    require_user,
)
from core.db import get_db
from core.webutil import HTTPException, parse, respond
from domain.models import (
    Campaign,
    CampaignMember,
    CampaignStatus,
    MemberRole,
    RuleApplies,
    RuleType,
    ScoringMode,
    Submission,
    SubmissionKind,
    User,
)
from domain.scoring import BULK_KIND_METRICS
from routers.common import (
    audit,
    get_campaign_or_404,
    get_or_create_user,
    load_submissions,
    submission_out,
)
from domain.schemas import SubmissionIn, SubmissionModerationIn

bp = Blueprint("submissions", __name__, url_prefix="/api")

WIKIDATA_DOMAIN = "www.wikidata.org"
COMMONS_DOMAIN = "commons.wikimedia.org"

# Bulk kinds: one submission covering the participant's activity in the
# campaign window. domain + canonical title (unique per user via
# uq_submission) + which rule applicability they piggyback on.
BULK_KINDS = {
    SubmissionKind.wikidata_edits: (WIKIDATA_DOMAIN, "Wikidata edits",
                                    RuleApplies.wikidata_item),
    SubmissionKind.commons_edits: (COMMONS_DOMAIN, "Commons uploads",
                                   RuleApplies.commons_file),
}


def _has_bulk_rules(campaign: Campaign, kind: SubmissionKind) -> bool:
    """A bulk kind is available only when the campaign carries active
    per_unit rules for its metrics (e.g. statements / depicts_added)."""
    metrics = set(BULK_KIND_METRICS[kind])
    applies = BULK_KINDS[kind][2]
    return any(
        r.active and r.rule_type == RuleType.per_unit
        and r.metric in metrics
        and r.applies_to in (RuleApplies.any, applies)
        for r in campaign.rules
    )


def _eligibility_any_of(campaign: Campaign) -> list[str]:
    """The "P17=Q668"-style constraints of the campaign's Wikidata
    eligibility rule, if one is configured."""
    for r in campaign.rules:
        if (r.active and r.rule_type == RuleType.eligibility
                and r.applies_to in (RuleApplies.any,
                                     RuleApplies.wikidata_item)
                and r.params):
            return list(r.params.get("any_of") or [])
    return []


def _depicts_targets(campaign: Campaign) -> list[str]:
    """Optional QID whitelist on the depicts rule (params.any_of):
    only depicts statements pointing at these items count."""
    for r in campaign.rules:
        if (r.active and r.rule_type == RuleType.per_unit
                and r.metric == "depicts_added" and r.params):
            return list(r.params.get("any_of") or [])
    return []


def _fetch_bulk_metrics(sub: Submission, campaign: Campaign,
                        username: str) -> None:
    """Best-effort activity counts for a bulk submission. Users whose
    edit volume exceeds the campaign's auto-scoring cap (QuickStatements
    / OpenRefine runs, mass uploads) get {"over_limit": true} instead of
    counts: the coordinator reviews the contributions and enters the
    points manually via the points override."""
    settings = campaign.effective_settings
    try:
        if sub.kind == SubmissionKind.wikidata_edits:
            cap = int(settings.get("max_wikidata_edits_auto", 50) or 0)
            activity = mediawiki.fetch_wikidata_user_activity(
                username, campaign.start_date, campaign.end_date,
                max_edits=cap or None)
            if activity is None:
                sub.metrics = {"over_limit": True, "limit": cap}
            else:
                eligible = (mediawiki.fetch_eligible_qids(
                    sorted(activity), _eligibility_any_of(campaign))
                    if activity else set())
                sub.metrics = {
                    "statements": sum(v["statements"]
                                      for q, v in activity.items()
                                      if q in eligible),
                    "terms": sum(v["terms"] for q, v in activity.items()
                                 if q in eligible),
                    "edited_qids": len(activity),
                    "eligible_qids": sorted(eligible),
                }
        else:
            cap = int(settings.get("max_commons_uploads_auto", 100) or 0)
            metrics = mediawiki.fetch_commons_user_activity(
                username, campaign.start_date, campaign.end_date,
                _depicts_targets(campaign), max_edits=cap or None)
            sub.metrics = (metrics if metrics is not None
                           else {"over_limit": True, "limit": cap})
    except Exception:
        return
    sub.metadata_fetched_at = datetime.now(timezone.utc)


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
    sub.wikidata_qid = meta.wikidata_qid
    sub.metadata_fetched_at = datetime.now(timezone.utc)
    if sub.kind == SubmissionKind.wikidata_item:
        _fetch_wikidata_item_metrics(sub, campaign, username)
    return meta


def _fetch_wikidata_item_metrics(sub: Submission, campaign: Campaign,
                                 username: str) -> None:
    """Statement/label/description/alias edit counts on this one item, for
    the "Statements added" / "Labels..." per_unit rules AND the
    suggested-list bonus's real-contribution gate (a title/QID match alone
    isn't a contribution — the submitter must have actually edited it)."""
    try:
        activity = mediawiki.fetch_wikidata_user_activity(
            username, campaign.start_date, campaign.end_date)
        entry = (activity or {}).get(sub.title.upper(),
                                     {"statements": 0, "terms": 0})
        sub.metrics = {"statements": entry["statements"], "terms": entry["terms"]}
    except Exception:
        pass


def _check_eligibility(sub: Submission, campaign: Campaign, user: User,
                       settings: dict,
                       meta: "mediawiki.PageMetadata | None") -> None:
    """Fountain-style eligibility rules, checked against fetched metadata.
    Checks that need metadata are skipped when the fetch failed — the
    organizer can still reject after a manual refresh."""
    # A confirmed "page does not exist on this wiki" is unambiguous and
    # always rejected — this is the guard against e.g. submitting a title
    # against the wrong project's domain in a multi-language campaign
    # (the title exists on one wiki, not the one actually selected).
    if meta is not None and not meta.exists:
        raise HTTPException(
            400, f"{sub.title!r} does not exist on {sub.wiki_domain}")
    if sub.metadata_fetched_at is not None:
        # Always enforced, not settings-gated: a submitter with zero
        # detected bytes_added who didn't create the page made no
        # verifiable contribution to it — without this, anyone could
        # submit any page/item (in particular one on the suggested list)
        # they never touched and still collect its auto-scored bonuses.
        # For Wikidata items, a statement/label edit doesn't always move
        # page size, so counted metrics are accepted as evidence too.
        metrics = sub.metrics or {}
        has_metrics = metrics.get("statements", 0) or metrics.get("terms", 0)
        if not sub.is_new_page and not sub.bytes_added and not has_metrics:
            raise HTTPException(
                400, "No edits by you were found on this page during the "
                     "campaign period")
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
    if (payload.kind == SubmissionKind.commons_file
            and not settings.get("allow_commons_files")):
        raise HTTPException(400,
                            "This campaign does not accept Commons files")
    if payload.kind in BULK_KINDS and not _has_bulk_rules(campaign,
                                                          payload.kind):
        raise HTTPException(
            400, "This campaign has no scoring rules for this "
                 "submission type")
    if payload.kind not in BULK_KINDS and not payload.title.strip():
        raise HTTPException(400, "A title is required")

    # Coordinators (organizers) may submit on behalf of another user.
    participant = user
    username = (payload.username or "").strip()
    if username and username != user.username:
        require_organizer(db, campaign, user)
        participant = get_or_create_user(db, username)

    roles = campaign_roles(db, campaign, participant)
    if MemberRole.jury in roles and not settings.get("jury_can_submit"):
        raise HTTPException(403, "Jury members cannot submit to this campaign")

    title = payload.title.strip()
    if payload.kind in BULK_KINDS:
        wiki_domain, title, _ = BULK_KINDS[payload.kind]
    elif payload.kind == SubmissionKind.wikidata_item:
        wiki_domain = WIKIDATA_DOMAIN
    elif payload.kind == SubmissionKind.commons_file:
        wiki_domain = COMMONS_DOMAIN
    elif payload.language and settings.get("multi_language"):
        # Multi-language campaign: the participant picks the wiki.
        wiki_domain = f"{payload.language}.wikipedia.org"
    else:
        wiki_domain = campaign.wiki_domain
    existing = db.query(Submission).filter_by(
        campaign_id=campaign.id, user_id=participant.id, title=title,
        wiki_domain=wiki_domain).first()
    if existing:
        raise HTTPException(409, "This page was already submitted for "
                                 "this participant")

    max_subs = int(settings.get("max_submissions_per_user", 0) or 0)
    if max_subs:
        count = db.query(Submission).filter_by(
            campaign_id=campaign.id, user_id=participant.id).count()
        if count >= max_subs:
            raise HTTPException(
                400, f"Submission limit of {max_subs} reached")

    sub = Submission(
        campaign_id=campaign.id, user_id=participant.id, kind=payload.kind,
        title=title, wiki_domain=wiki_domain,
    )
    if payload.kind in BULK_KINDS:
        _fetch_bulk_metrics(sub, campaign, participant.username)
    else:
        meta = _fetch_metadata(sub, campaign, participant.username)
        _check_eligibility(sub, campaign, participant, settings, meta)
    db.add(sub)

    if MemberRole.participant not in roles:
        db.add(CampaignMember(campaign_id=campaign.id, user_id=participant.id,
                              role=MemberRole.participant, added_by=user.id))
    details = {"campaign": slug, "title": title}
    if participant.id != user.id:
        details["on_behalf_of"] = participant.username

    # Optional campaign template, written to the wiki with the submitting
    # account's OAuth token (best-effort — never blocks the submission).
    template = (settings.get("template_name") or "").strip()
    if (settings.get("auto_add_template") and template
            and payload.kind == SubmissionKind.article):
        token = get_session_oauth_token()
        added = False
        if token:
            try:
                added = mediawiki.add_page_template(
                    wiki_domain, title, template,
                    settings.get("template_placement", "talk") != "article",
                    token)
            except Exception:
                added = False
        details["template_added"] = added

    audit(db, user, "submit", "submission", None, details)
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


@bp.get("/submissions/<int:submission_id>/details")
def submission_details(submission_id: int):
    """Live per-article facts for the expanded submission card: size,
    word count, creation/last-edit dates and editors. Fetched on demand
    (only while the card is expanded) rather than eagerly for every
    submission in the list."""
    db = get_db()
    sub = _get_submission_or_404(db, submission_id)
    try:
        if sub.kind == SubmissionKind.article:
            details = mediawiki.fetch_article_details(sub.wiki_domain, sub.title)
        elif sub.kind == SubmissionKind.wikidata_item:
            details = mediawiki.fetch_wikidata_details(sub.title)
        elif sub.kind == SubmissionKind.commons_file:
            details = mediawiki.fetch_commons_details(sub.title)
        else:
            details = sub.metrics
    except Exception:
        raise HTTPException(502, "Could not fetch details from the wiki")
    return respond(details)


@bp.post("/submissions/<int:submission_id>/refresh")
def refresh_metadata(submission_id: int):
    db, user = get_db(), require_user()
    sub = _get_submission_or_404(db, submission_id)
    campaign = sub.campaign
    if sub.user_id != user.id:
        require_organizer(db, campaign, user)
    if sub.kind in BULK_KINDS:
        _fetch_bulk_metrics(sub, campaign, sub.user.username)
    else:
        _fetch_metadata(sub, campaign, sub.user.username)
    db.commit()
    db.refresh(sub)
    return respond(submission_out(campaign, sub))


@bp.post("/submissions/<int:submission_id>/recalculate")
def recalculate_points(submission_id: int):
    """Refetch the wiki metadata and score the submission from the
    campaign rules again — e.g. after the participant made more edits.
    Owners may recalculate their own submission, but only to pick up
    fresh metadata: an organizer's manual points override is a deliberate
    decision and stays in effect until an organizer clears it themself.
    A coordinator's recalculation does clear it, same as before."""
    db, user = get_db(), require_user()
    sub = _get_submission_or_404(db, submission_id)
    campaign = sub.campaign
    is_owner = sub.user_id == user.id
    if not is_owner:
        require_organizer(db, campaign, user)
    if sub.kind in BULK_KINDS:
        _fetch_bulk_metrics(sub, campaign, sub.user.username)
    else:
        _fetch_metadata(sub, campaign, sub.user.username)
    had_override = sub.points_override is not None
    if not is_owner:
        sub.points_override = None
    audit(db, user, "recalculate", "submission", sub.id,
          {"campaign": campaign.slug, "title": sub.title,
           "cleared_override": had_override and not is_owner})
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
    if payload.moderation_note is not None:
        sub.moderation_note = payload.moderation_note.strip() or None
    if payload.clear_override:
        sub.points_override = None
    elif payload.points_override is not None:
        sub.points_override = payload.points_override
    audit(db, user, "moderate", "submission", sub.id,
          {"campaign": campaign.slug, "title": sub.title,
           "status": sub.status.value,
           "moderation_note": sub.moderation_note,
           "points_override": (float(sub.points_override)
                               if sub.points_override is not None else None)})
    db.commit()
    db.refresh(sub)
    return respond(submission_out(campaign, sub))

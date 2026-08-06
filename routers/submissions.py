"""Submissions: participants add their contributions to a campaign.

Identity always comes from the session. Submitting auto-joins the
campaign as participant (same flow in jury and self modes). Page
metadata is fetched from the MediaWiki API at submission time and can
be refreshed; a failed fetch never blocks the submission.
"""
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone

from flask import Blueprint, request
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

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
    Review,
    RuleApplies,
    RuleType,
    ScoringMode,
    Submission,
    SubmissionKind,
    SubmissionStatus,
    User,
)
from domain.scoring import BULK_KIND_METRICS, normalize_title
from routers.common import (
    audit,
    can_see_campaign,
    ensure_scored,
    get_campaign_or_404,
    get_or_create_user,
    load_submissions,
    rescore_submission,
    submission_out,
    suggested_titles,
)
from domain.schemas import (SubmissionIn, SubmissionListOut,
                            SubmissionModerationIn)

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


# MediaWiki refuses these outright in page titles; a submission carrying
# one is never a real page, so it is rejected before any API call rather
# than relying on the best-effort metadata fetch to notice.
_BAD_TITLE_CHARS = set("#<>[]|{}_")
_QID_RE = re.compile(r"^Q[1-9]\d*$")
_FILE_RE = re.compile(r"^(?:File|Image):.+\.[A-Za-z0-9]{2,5}$")


def _validate_title(kind: SubmissionKind, title: str) -> str:
    """Reject anything that cannot name a real page before it is stored.

    Without this a participant can paste arbitrary text (a SPARQL query,
    a sentence) and have it accepted: MediaWiki reports such a title as
    "invalid" rather than "missing", and a metadata fetch that fails for
    any reason leaves the eligibility checks with nothing to test.
    """
    if kind == SubmissionKind.wikidata_item:
        qid = title.upper()
        if not _QID_RE.match(qid):
            raise HTTPException(
                400, "A Wikidata submission must be an item ID like Q42")
        return qid
    if kind == SubmissionKind.commons_file:
        if not _FILE_RE.match(title):
            raise HTTPException(
                400, "A Commons submission must be a file name like "
                     "File:Example.jpg")
    if len(title) > 255:
        raise HTTPException(400, "The title is too long to be a page name")
    if _BAD_TITLE_CHARS & set(title):
        raise HTTPException(
            400, "The title contains characters that cannot appear in a "
                 "page name — enter the page title exactly as it appears "
                 "on the wiki")
    return title


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


def _individually_submitted_qids(db: Session, campaign: Campaign,
                                 user_id: int) -> set[str]:
    """QIDs this user already submitted individually in this campaign.

    Their edits are scored on those submissions, so counting them again in
    the user's bulk total would pay twice for the same work."""
    rows = db.query(Submission.title).filter(
        Submission.campaign_id == campaign.id,
        Submission.user_id == user_id,
        Submission.kind == SubmissionKind.wikidata_item,
        Submission.status != SubmissionStatus.rejected,
    ).all()
    return {(t or "").strip().upper() for (t,) in rows}


def _fetch_bulk_metrics(sub: Submission, campaign: Campaign,
                        username: str, db: Session | None = None) -> None:
    """Best-effort activity counts for a bulk submission. Users whose
    edit volume exceeds the campaign's auto-scoring cap (QuickStatements
    / OpenRefine runs, mass uploads) get {"over_limit": true} instead of
    counts: the coordinator reviews the contributions and enters the
    points manually via the points override."""
    settings = campaign.effective_settings
    try:
        if sub.kind == SubmissionKind.wikidata_edits:
            # Only wikidata_edit_limit_single is honoured here. The former
            # key is deliberately not consulted as a fallback: campaigns
            # carry stale overrides for it from when its default was lower,
            # and reading those is what made recalculating a heavy editor
            # fail however often it was retried.
            cap = int(settings.get("wikidata_edit_limit_single") or 0)
            activity = mediawiki.fetch_wikidata_user_activity(
                username, campaign.start_date, campaign.end_date,
                max_edits=cap or None)
            if activity is None:
                sub.metrics = {"over_limit": True, "limit": cap}
            else:
                # Items the user submitted on their own are scored there;
                # drop them here so the same edits are not paid twice.
                own = (_individually_submitted_qids(db, campaign, sub.user_id)
                       if db is not None else set())
                excluded = sorted(own & set(activity))
                activity = {q: v for q, v in activity.items() if q not in own}
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
                    "excluded_qids": excluded,
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
        entry = mediawiki.fetch_item_user_edits(
            sub.title.upper(), username,
            campaign.start_date, campaign.end_date)
        sub.metrics = {"statements": entry["statements"],
                       "terms": entry["terms"]}
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
        # Optional: restrict individual Wikidata item submissions to the
        # campaign's suggested list, so participants work the curated
        # backlog rather than any item they happen to have edited. Bulk
        # wikidata_edits submissions are unaffected — those are gated by
        # the property/eligibility constraints instead.
        if (settings.get("suggested_items_only")
                and sub.kind == SubmissionKind.wikidata_item):
            listed = suggested_titles(campaign, SubmissionKind.wikidata_item)
            title = (sub.title or "").strip().upper()
            if normalize_title(sub.title) not in listed and title not in listed:
                raise HTTPException(
                    400, "This campaign only accepts Wikidata items from its "
                         "suggested list")
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
                and not mediawiki.same_user(meta.creator, user.username)):
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


# The list endpoint pages on the server: a large campaign's submissions
# never travel (or get scored) wholesale for one screen. Page size is
# capped; consumers that legitimately need "everything of one narrow
# kind" (the bulk tab, a jury group expand) use the higher cap with a
# kind/user filter, which bounds the rows to one per participant anyway.
PAGE_SIZE_DEFAULT = 50
PAGE_SIZE_MAX = 500

# Review-state filters, mirrored from the frontend's backlog dropdown.
# "awaiting_me" additionally excludes the caller's own submissions — you
# can never review yourself, so they would sit in the queue forever.
def _review_filter(q, state: str, user: User | None):
    if state == "awaiting_me":
        if user is None:
            raise HTTPException(401, "Login required for this filter")
        return q.filter(
            Submission.user_id != user.id,
            Submission.status != SubmissionStatus.rejected,
            ~Submission.reviews.any(Review.reviewer_id == user.id))
    if state == "unreviewed":
        return q.filter(Submission.status != SubmissionStatus.rejected,
                        ~Submission.reviews.any())
    if state == "not_accepted":
        return q.filter(Submission.status == SubmissionStatus.submitted)
    if state == "rejected":
        return q.filter(Submission.status == SubmissionStatus.rejected)
    raise HTTPException(400, f"Unknown review filter {state!r}")


def _int_arg(name: str, default: int, lo: int, hi: int) -> int:
    try:
        value = int(request.args.get(name, default) or default)
    except ValueError:
        raise HTTPException(400, f"{name} must be a number")
    return min(max(value, lo), hi)


def _submission_facets(db: Session, campaign: Campaign,
                       user: User | None) -> dict:
    """Campaign-wide counts for the filter dropdowns. Computed over the
    non-bulk submissions (the paged list never shows bulk kinds), so a
    dropdown always describes the whole campaign, not the current page."""
    def base():
        return (db.query(Submission)
                .filter(Submission.campaign_id == campaign.id,
                        ~Submission.kind.in_(list(BULK_KINDS))))

    kinds = dict(
        base().with_entities(Submission.kind, func.count(Submission.id))
        .group_by(Submission.kind).all())
    domains = [d for (d,) in
               base().filter(Submission.kind == SubmissionKind.article)
               .with_entities(Submission.wiki_domain).distinct().all()]
    participants = [
        n for (n,) in
        base().join(User, Submission.user_id == User.id)
        .with_entities(User.username).distinct().order_by(User.username).all()
    ]
    review = {
        "unreviewed": _review_filter(base(), "unreviewed", user).count(),
        "not_accepted": _review_filter(base(), "not_accepted", user).count(),
        "rejected": _review_filter(base(), "rejected", user).count(),
    }
    if user is not None:
        review["awaiting_me"] = _review_filter(base(), "awaiting_me",
                                               user).count()
    return {
        "kinds": {k.value: n for k, n in kinds.items()},
        "languages": sorted({d.split(".")[0] for d in domains}),
        "participants": participants,
        "review": review,
    }


def _marks_hidden(db: Session, campaign: Campaign, user: User | None,
                  settings: dict) -> bool:
    """Fountain's HiddenMarks: in anonymous-review campaigns only
    organizers/admins see marks and points; jurors additionally see
    their own review."""
    if not settings.get("anonymous_reviews"):
        return False
    return not (user is not None and (
        user.is_admin
        or MemberRole.organizer in campaign_roles(db, campaign, user)))


@bp.get("/campaigns/<slug>/submissions")
def list_submissions(slug: str):
    """One page of a campaign's submissions.

    Rows are lean by default — stored columns plus the cached points, one
    SQL query, no scoring at read time. The expanded card fetches the
    full detail (breakdown, reviews, claims) per submission; the judging
    screen passes detail=1 to get today's full rows for its page.

    Query parameters (all optional):
      page, per_page   1-based page and its size (capped)
      kind             one submission kind
      exclude_bulk     leave out the bulk kinds (the submissions screen)
      user             one participant's username
      mine             only the caller's own submissions
      language         articles from this Wikipedia language
      review           awaiting_me | unreviewed | not_accepted | rejected
      facets           include campaign-wide filter counts
      detail           full rows with reviews/claims/breakdown
    """
    db, user = get_db(), get_current_user()
    campaign = get_campaign_or_404(db, slug)
    settings = campaign.effective_settings
    ensure_scored(db, campaign)

    q = db.query(Submission).filter(Submission.campaign_id == campaign.id)
    kind = request.args.get("kind", "").strip()
    if kind:
        try:
            q = q.filter(Submission.kind == SubmissionKind(kind))
        except ValueError:
            raise HTTPException(400, f"Unknown submission kind {kind!r}")
    if request.args.get("exclude_bulk"):
        q = q.filter(~Submission.kind.in_(list(BULK_KINDS)))
    if request.args.get("mine"):
        q = q.filter(Submission.user_id == (user.id if user else -1))
    username = request.args.get("user", "").strip()
    if username:
        q = q.filter(Submission.user.has(User.username == username))
    language = request.args.get("language", "").strip().lower()
    if language:
        q = q.filter(Submission.kind == SubmissionKind.article,
                     Submission.wiki_domain.startswith(f"{language}."))
    review_state = request.args.get("review", "").strip()
    if review_state:
        q = _review_filter(q, review_state, user)

    page = _int_arg("page", 1, 1, 1_000_000)
    per_page = _int_arg("per_page", PAGE_SIZE_DEFAULT, 1, PAGE_SIZE_MAX)
    total = q.count()
    detail = bool(request.args.get("detail"))
    options = [selectinload(Submission.user)]
    if detail:
        options += [
            # reviewer included: serializing a review names its reviewer,
            # and without this every review row costs its own SELECT.
            selectinload(Submission.reviews).selectinload(Review.reviewer),
            selectinload(Submission.claims),
        ]
    subs = (
        q.options(*options)
        .order_by(Submission.submitted_at.desc(), Submission.id.desc())
        .offset((page - 1) * per_page).limit(per_page)
        .all()
    )

    hidden = _marks_hidden(db, campaign, user, settings)
    if detail:
        out = [submission_out(campaign, s, settings) for s in subs]
        if hidden:
            for item in out:
                item.reviews = [r for r in item.reviews
                                if user and r.reviewer.id == user.id]
                if campaign.scoring_mode == ScoringMode.jury:
                    item.points = 0
                    item.breakdown = []
    else:
        out = []
        for s in subs:
            row = SubmissionListOut.model_validate(s)
            row.points = float(s.points_cached or 0)
            if hidden and campaign.scoring_mode == ScoringMode.jury:
                row.points = 0
            out.append(row)

    payload = {
        "items": out,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, -(-total // per_page)),
    }
    if request.args.get("facets"):
        payload["facets"] = _submission_facets(db, campaign, user)
    return respond(payload)


@bp.get("/submissions/<int:submission_id>")
def get_submission(submission_id: int):
    """Full detail of one submission — points breakdown, reviews and
    claims — for the expanded card. The paged list stays lean."""
    db, user = get_db(), get_current_user()
    sub = _get_submission_or_404(db, submission_id)
    campaign = sub.campaign
    if not can_see_campaign(db, campaign, user):
        raise HTTPException(404, "Submission not found")
    settings = campaign.effective_settings
    out = submission_out(campaign, sub, settings)
    if _marks_hidden(db, campaign, user, settings):
        out.reviews = [r for r in out.reviews
                       if user and r.reviewer.id == user.id]
        if campaign.scoring_mode == ScoringMode.jury:
            out.points = 0
            out.breakdown = []
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
    if payload.kind not in BULK_KINDS:
        title = _validate_title(payload.kind, title)
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
        _fetch_bulk_metrics(sub, campaign, participant.username, db)
    else:
        meta = _fetch_metadata(sub, campaign, participant.username)
        _check_eligibility(sub, campaign, participant, settings, meta)
    db.add(sub)
    rescore_submission(campaign, sub, settings)

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


@bp.get("/submissions/<int:submission_id>/preview")
def submission_preview(submission_id: int):
    """Quick-glance preview for the popup: rendered lead section for an
    article, or label/description/claims for a Wikidata item. Commons
    files and bulk kinds have no dedicated preview — the frontend links
    out to the wiki directly for those."""
    db = get_db()
    sub = _get_submission_or_404(db, submission_id)
    try:
        if sub.kind == SubmissionKind.article:
            preview = mediawiki.fetch_article_preview(sub.wiki_domain, sub.title)
        elif sub.kind == SubmissionKind.wikidata_item:
            preview = mediawiki.fetch_wikidata_preview(sub.title)
        else:
            raise HTTPException(400, "No preview available for this submission type")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(502, "Could not fetch a preview from the wiki")
    if preview is None:
        raise HTTPException(404, "Not found on the wiki")
    return respond(preview)


@bp.get("/campaigns/<slug>/submissions/english-names")
def submission_english_names(slug: str):
    """English name for every non-English submission in one batch: the
    label for Wikidata items, and the connected item's English sitelink
    title for non-English articles. Two Wikidata calls total (pageprops
    lookups happen per wiki_domain) instead of one per submission row, so
    the submissions list can show "native title (English name)" without
    an expensive per-row fetch.

    ?ids=1,2,3 restricts the lookup to those submissions — the list is
    paged now, so the frontend asks for the rows on screen instead of
    the whole campaign."""
    db = get_db()
    campaign = get_campaign_or_404(db, slug)
    ids_raw = request.args.get("ids", "")
    if ids_raw:
        ids = [int(x) for x in ids_raw.split(",") if x.strip().isdigit()]
        subs = (db.query(Submission)
                .filter(Submission.campaign_id == campaign.id,
                        Submission.id.in_(ids[:PAGE_SIZE_MAX]))
                .all()) if ids else []
    else:
        subs = load_submissions(db, campaign.id)

    out: dict[int, dict] = {}
    item_subs = [s for s in subs if s.kind == SubmissionKind.wikidata_item]
    article_subs = [s for s in subs if s.kind == SubmissionKind.article
                    and s.wiki_domain.split(".")[0] != "en"]

    qids = list({s.title.upper() for s in item_subs})
    # non-English articles: resolve each domain's titles -> connected QIDs
    article_qids: dict[int, str] = {}
    by_domain: dict[str, list[Submission]] = {}
    for s in article_subs:
        by_domain.setdefault(s.wiki_domain, []).append(s)
    try:
        for domain, group in by_domain.items():
            qid_by_title = mediawiki.fetch_wikibase_items(
                domain, [s.title for s in group])
            for s in group:
                qid = qid_by_title.get(s.title)
                if qid:
                    article_qids[s.id] = qid

        all_qids = list({*qids, *article_qids.values()})
        entities = mediawiki.fetch_sitelinks(all_qids, ["en"]) if all_qids else {}

        for s in item_subs:
            entity = entities.get(s.title.upper())
            if entity and entity.get("label_en"):
                out[s.id] = {"label_en": entity["label_en"]}
        for s in article_subs:
            qid = article_qids.get(s.id)
            entity = entities.get(qid) if qid else None
            if entity:
                title_en = entity.get("links", {}).get("en")
                if title_en and title_en != s.title:
                    out[s.id] = {"title_en": title_en}
    except Exception:
        raise HTTPException(502, "Could not reach Wikidata for English names")
    return respond(out)


@bp.post("/submissions/<int:submission_id>/refresh")
def refresh_metadata(submission_id: int):
    db, user = get_db(), require_user()
    sub = _get_submission_or_404(db, submission_id)
    campaign = sub.campaign
    if sub.user_id != user.id:
        require_organizer(db, campaign, user)
    if sub.kind in BULK_KINDS:
        _fetch_bulk_metrics(sub, campaign, sub.user.username, db)
    else:
        _fetch_metadata(sub, campaign, sub.user.username)
    rescore_submission(campaign, sub)
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
        _fetch_bulk_metrics(sub, campaign, sub.user.username, db)
    else:
        _fetch_metadata(sub, campaign, sub.user.username)
    had_override = sub.points_override is not None
    if not is_owner:
        sub.points_override = None
    rescore_submission(campaign, sub)
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
    rescore_submission(campaign, sub)
    audit(db, user, "moderate", "submission", sub.id,
          {"campaign": campaign.slug, "title": sub.title,
           "status": sub.status.value,
           "moderation_note": sub.moderation_note,
           "points_override": (float(sub.points_override)
                               if sub.points_override is not None else None)})
    db.commit()
    db.refresh(sub)
    return respond(submission_out(campaign, sub))


def _wikidata_activity_for(username: str, campaign_start, campaign_end,
                           cap: int) -> tuple[dict | None, bool]:
    """One user's raw Wikidata activity. Plain arguments and a plain
    return value only: this runs on a worker thread, which has neither the
    request's DB session nor safe access to ORM objects."""
    try:
        activity = mediawiki.fetch_wikidata_user_activity(
            username, campaign_start, campaign_end, max_edits=cap or None)
        return activity, False
    except Exception:
        return None, True


@bp.post("/campaigns/<slug>/bulk-wikidata/recalculate-all")
def recalculate_all_bulk_wikidata(slug: str):
    """Refresh every Wikidata bulk submission in the campaign.

    Each participant's counts come from their own contribution history, so
    there is no batch API to ask once — this is inherently a loop over
    users. Walking them one after another takes a paginated round-trip
    each and gets slow well before a campaign's fortieth participant, so
    the wiki fetches run concurrently and only the results are applied
    here, on the request thread that owns the session.

    Only existing bulk submissions are refreshed; adding a missing one
    stays a deliberate per-participant action.
    """
    db, user = get_db(), require_user()
    campaign = get_campaign_or_404(db, slug)
    require_organizer(db, campaign, user)

    subs = db.query(Submission).filter_by(
        campaign_id=campaign.id,
        kind=SubmissionKind.wikidata_edits).all()
    if not subs:
        return respond({"refreshed": 0, "skipped": 0, "failed": 0,
                        "total": 0, "cap": 0})

    # The sweep walks every participant inside one request, so it uses the
    # lower cap: a heavy editor costs ~1 s per 500 edits, and the whole
    # campaign has to come back before the request times out. Recalculating
    # one participant is not bounded that way and uses the higher cap.
    settings = campaign.effective_settings
    cap = int(settings.get("max_wikidata_edits_sweep") or 0)
    names = [s.user.username for s in subs]
    with ThreadPoolExecutor(max_workers=min(16, len(names))) as pool:
        fetched = list(pool.map(
            lambda n: _wikidata_activity_for(n, campaign.start_date,
                                             campaign.end_date, cap), names))

    any_of = _eligibility_any_of(campaign)
    refreshed = skipped = failed = 0
    for sub, (activity, error) in zip(subs, fetched):
        if error:
            failed += 1
            continue
        if activity is None:
            # Past the sweep's cap. Left exactly as it was: overwriting good
            # counts with {"over_limit": true} would destroy a score the
            # higher individual cap can still compute. Recalculate this
            # participant on their own row instead.
            skipped += 1
            continue
        own = _individually_submitted_qids(db, campaign, sub.user_id)
        excluded = sorted(own & set(activity))
        activity = {q: v for q, v in activity.items() if q not in own}
        try:
            eligible = (mediawiki.fetch_eligible_qids(sorted(activity), any_of)
                        if activity else set())
        except Exception:
            failed += 1
            continue
        sub.metrics = {
            "statements": sum(v["statements"] for q, v in activity.items()
                              if q in eligible),
            "terms": sum(v["terms"] for q, v in activity.items()
                         if q in eligible),
            "edited_qids": len(activity),
            "eligible_qids": sorted(eligible),
            "excluded_qids": excluded,
        }
        sub.metadata_fetched_at = datetime.now(timezone.utc)
        rescore_submission(campaign, sub, settings)
        refreshed += 1

    audit(db, user, "recalculate_bulk_all", "campaign", campaign.id,
          {"campaign": slug, "refreshed": refreshed,
           "skipped": skipped, "failed": failed})
    db.commit()
    return respond({"refreshed": refreshed, "skipped": skipped,
                    "failed": failed, "total": len(subs), "cap": cap})

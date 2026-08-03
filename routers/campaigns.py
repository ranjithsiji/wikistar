"""Campaign CRUD, lifecycle, membership, leaderboard and statistics.

Permissions
-----------
list/detail/stats    public (draft/rejected visible to organizer+admin only)
create               any logged-in user; creator becomes organizer
update               organizer or admin
delete               admin, or organizer while still draft
approve/reject       admin
join                 any logged-in user (both jury and self modes)
leaderboard          public unless show_leaderboard is off
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, request
from sqlalchemy import func
from sqlalchemy.orm import Session

from integrations import mediawiki, wiki_rights
from domain import settings_registry
from auth import (
    campaign_roles,
    get_current_user,
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
    ScoringMode,
    ScoringRule,
    Submission,
    SubmissionKind,
    SuggestedPage,
    User,
)
from routers.common import (
    audit,
    campaign_counts,
    campaign_detail_out,
    campaign_summary,
    can_see_campaign,
    compute_leaderboard,
    get_campaign_or_404,
    get_or_create_user,
    load_submissions,
    suggested_titles,
    visible_campaigns,
)
from domain.schemas import CampaignIn, CampaignStats, MemberAddIn
from domain.scoring import (
    compute_breakdown,
    default_self_assessment_rules,
    normalize_title,
)

bp = Blueprint("campaigns", __name__, url_prefix="/api")


@bp.get("/meta")
def meta():
    """Static metadata the frontend needs to render forms."""
    return respond({
        "settings_registry": settings_registry.SETTING_DEFS,
        "default_rules": {"self": default_self_assessment_rules()},
        "scoring_modes": ["jury", "self", "hybrid"],
    })


@bp.get("/stats")
def site_stats():
    """Public headline numbers for the homepage hero."""
    db = get_db()
    public = ~Campaign.status.in_((CampaignStatus.draft,
                                   CampaignStatus.rejected))
    return respond({
        "campaigns": db.query(func.count(Campaign.id)).filter(public).scalar(),
        "live_campaigns": db.query(func.count(Campaign.id))
            .filter(Campaign.status == CampaignStatus.active).scalar(),
        "participants": db.query(func.count(func.distinct(CampaignMember.user_id)))
            .filter(CampaignMember.role == MemberRole.participant).scalar(),
        "submissions": db.query(func.count(Submission.id)).scalar(),
    })


@bp.get("/campaigns")
def list_campaigns():
    db, user = get_db(), get_current_user()
    campaigns = db.query(Campaign).order_by(Campaign.start_date.desc()).all()
    visible = visible_campaigns(db, campaigns, user)
    counts = campaign_counts(db, visible)
    return respond([campaign_summary(db, c, counts[c.id]) for c in visible])


def _validated_settings(payload: CampaignIn) -> dict:
    try:
        return settings_registry.validate_overrides(payload.settings)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


def _apply_scalar_fields(campaign: Campaign, payload: CampaignIn) -> None:
    if payload.end_date < payload.start_date:
        raise HTTPException(400, "end_date must not be before start_date")
    campaign.name = payload.name
    campaign.description = payload.description
    campaign.language = payload.language
    campaign.wiki_domain = (payload.wiki_domain
                            or f"{payload.language}.wikipedia.org")
    campaign.start_date = payload.start_date
    campaign.end_date = payload.end_date
    campaign.scoring_mode = payload.scoring_mode


def _replace_jury(db: Session, campaign: Campaign, usernames: list[str],
                  acting: User) -> None:
    wanted = {u.strip() for u in usernames if u.strip()}
    current = {m.user.username: m for m in campaign.members
               if m.role == MemberRole.jury}
    for username, member in current.items():
        if username not in wanted:
            db.delete(member)
    for username in wanted - set(current):
        member_user = get_or_create_user(db, username)
        db.add(CampaignMember(campaign_id=campaign.id, user_id=member_user.id,
                              role=MemberRole.jury, added_by=acting.id))


def _replace_coordinators(db: Session, campaign: Campaign,
                          usernames: list[str], acting: User) -> None:
    """Sync the organizer role to the given usernames. The campaign's
    creator always keeps the role."""
    db.flush()
    wanted = {u.strip() for u in usernames if u.strip()}
    creator = db.get(User, campaign.created_by) if campaign.created_by else None
    if creator is not None:
        wanted.add(creator.username)
    current = {
        m.user.username: m
        for m in db.query(CampaignMember)
        .filter_by(campaign_id=campaign.id, role=MemberRole.organizer).all()
    }
    for username, member in current.items():
        if username not in wanted:
            db.delete(member)
    for username in wanted - set(current):
        member_user = get_or_create_user(db, username)
        db.add(CampaignMember(campaign_id=campaign.id, user_id=member_user.id,
                              role=MemberRole.organizer, added_by=acting.id))


def _replace_suggested(campaign: Campaign, payload: CampaignIn) -> None:
    """Sync suggested pages in place: wholesale replacement would flush
    the new inserts before the deletes and trip uq_suggested. Articles
    have no section; Wikidata items carry an optional heading."""
    articles = {t.strip(): "" for t in payload.suggested_articles if t.strip()}
    items = {}
    for it in payload.suggested_items:
        qid = it.qid.strip()
        if qid:
            items.setdefault(qid, (it.section or "").strip())  # first wins
    wanted = (
        [(SubmissionKind.article, t, "") for t in articles]
        + [(SubmissionKind.wikidata_item, q, s) for q, s in items.items()]
    )
    wanted_keys = {(k, t) for k, t, _ in wanted}
    existing = {(p.kind, p.title): p for p in campaign.suggested_pages}
    for key, page in existing.items():
        if key not in wanted_keys:
            campaign.suggested_pages.remove(page)
    for kind, title, section in wanted:
        page = existing.get((kind, title))
        if page is None:
            campaign.suggested_pages.append(
                SuggestedPage(kind=kind, title=title, section=section))
        else:
            page.section = section  # section edits apply to kept rows
    _resolve_suggested_qids(campaign)


def _resolve_suggested_qids(campaign: Campaign) -> None:
    """Cache each suggested *article*'s connected Wikidata item.

    Scoring matches submitted articles to the suggested list by QID, so
    the bonus is independent of how a title was spelled and of which
    language edition the participant wrote in. Resolving here (once, when
    the list is saved) keeps scoring a pure function of stored data.

    Best-effort: a failed lookup leaves qid empty, and a suggested
    article with no QID simply cannot be matched — the same rule that
    applies to submissions. Re-saving the campaign retries the lookup.
    """
    pending = [p for p in campaign.suggested_pages
               if p.kind == SubmissionKind.article and not p.qid]
    if not pending:
        return
    try:
        qid_by_title = mediawiki.fetch_wikibase_items(
            campaign.wiki_domain, [p.title for p in pending])
    except Exception:
        return
    # The wiki answers under its own normalised spelling of each title,
    # so look results up by normalised key rather than verbatim.
    by_norm = {normalize_title(t): q for t, q in qid_by_title.items()}
    for page in pending:
        qid = by_norm.get(normalize_title(page.title))
        if qid:
            page.qid = qid


def _replace_rules(db: Session, campaign: Campaign, payload: CampaignIn) -> None:
    """Upsert rules by id. Removed rules are deleted unless claims
    reference them, in which case they are deactivated to keep history."""
    from domain.models import Claim

    existing = {r.id: r for r in campaign.rules}
    kept_ids: set[int] = set()
    for position, rule_in in enumerate(payload.rules):
        data = rule_in.model_dump(exclude={"id"})
        if rule_in.id and rule_in.id in existing:
            rule = existing[rule_in.id]
            for key, value in data.items():
                setattr(rule, key, value)
            rule.position = position
            kept_ids.add(rule.id)
        else:
            db.add(ScoringRule(campaign_id=campaign.id, position=position,
                               **data))
    for rule_id, rule in existing.items():
        if rule_id in kept_ids:
            continue
        referenced = db.query(Claim.id).filter_by(rule_id=rule_id).first()
        if referenced:
            rule.active = False
        else:
            db.delete(rule)


@bp.post("/campaigns")
def create_campaign():
    db, user = get_db(), require_user()
    payload = parse(CampaignIn)
    overrides = _validated_settings(payload)
    # The slug is chosen by the organizer (schema-validated to [a-z0-9-]),
    # so a collision is reported rather than silently renamed to "-2":
    # they asked for this exact public URL.
    if db.query(Campaign.id).filter_by(slug=payload.slug).first():
        raise HTTPException(409, f"The URL slug {payload.slug!r} is already taken")
    campaign = Campaign(slug=payload.slug, status=CampaignStatus.draft,
                        created_by=user.id)
    _apply_scalar_fields(campaign, payload)
    # Fountain model: creators holding the required on-wiki admin right
    # publish immediately (jury: sysop on the target wiki; self/hybrid:
    # sysop on any Wikipedia project); everyone else starts as a draft.
    auto_ok, auto_reason = wiki_rights.can_approve_campaign(user, campaign)
    if auto_ok:
        campaign.status = CampaignStatus.active
    db.add(campaign)
    db.flush()
    campaign.set_settings(overrides)
    db.add(CampaignMember(campaign_id=campaign.id, user_id=user.id,
                          role=MemberRole.organizer, added_by=user.id))
    _replace_coordinators(db, campaign, payload.coordinator_usernames, user)
    _replace_jury(db, campaign, payload.jury_usernames, user)
    _replace_suggested(campaign, payload)
    _replace_rules(db, campaign, payload)
    audit(db, user, "create", "campaign", campaign.id,
          {"slug": campaign.slug, "name": campaign.name,
           "auto_approved": auto_ok and auto_reason or False})
    db.commit()
    db.refresh(campaign)
    return respond(campaign_detail_out(db, campaign, user), 201)


@bp.get("/campaigns/<slug>")
def campaign_detail(slug: str):
    db, user = get_db(), get_current_user()
    campaign = get_campaign_or_404(db, slug)
    if not can_see_campaign(db, campaign, user):
        raise HTTPException(404, "Campaign not found")
    return respond(campaign_detail_out(db, campaign, user))


# Transitions organizers may perform themselves; admins may do anything.
ORGANIZER_TRANSITIONS = {
    (CampaignStatus.active, CampaignStatus.finished),
    (CampaignStatus.finished, CampaignStatus.active),
    (CampaignStatus.finished, CampaignStatus.archived),
}


@bp.put("/campaigns/<slug>")
def update_campaign(slug: str):
    db, user = get_db(), require_user()
    payload = parse(CampaignIn)
    campaign = get_campaign_or_404(db, slug)
    require_organizer(db, campaign, user)
    overrides = _validated_settings(payload)

    if payload.slug != campaign.slug:
        taken = db.query(Campaign.id).filter(
            Campaign.slug == payload.slug, Campaign.id != campaign.id).first()
        if taken:
            raise HTTPException(
                409, f"The URL slug {payload.slug!r} is already taken")
        campaign.slug = payload.slug
    if payload.status and payload.status != campaign.status:
        transition = (campaign.status, payload.status)
        if not user.is_admin and transition not in ORGANIZER_TRANSITIONS:
            raise HTTPException(
                403,
                f"Only an admin can move a campaign from "
                f"{campaign.status.value} to {payload.status.value}")
        campaign.status = payload.status

    _apply_scalar_fields(campaign, payload)
    campaign.set_settings(overrides)
    _replace_coordinators(db, campaign, payload.coordinator_usernames, user)
    _replace_jury(db, campaign, payload.jury_usernames, user)
    _replace_suggested(campaign, payload)
    _replace_rules(db, campaign, payload)
    audit(db, user, "update", "campaign", campaign.id, {"slug": campaign.slug})
    db.commit()
    db.refresh(campaign)
    return respond(campaign_detail_out(db, campaign, user))


@bp.delete("/campaigns/<slug>")
def delete_campaign(slug: str):
    db, user = get_db(), require_user()
    campaign = get_campaign_or_404(db, slug)
    if not user.is_admin:
        require_organizer(db, campaign, user)
        if campaign.status != CampaignStatus.draft:
            raise HTTPException(
                403, "Only draft campaigns can be deleted by their organizer")
    audit(db, user, "delete", "campaign", campaign.id,
          {"slug": campaign.slug, "name": campaign.name})
    db.delete(campaign)
    db.commit()
    return respond(None, 204)


@bp.post("/campaigns/<slug>/join")
def join_campaign(slug: str):
    """Join as a participant — works the same in jury and self modes."""
    db, user = get_db(), require_user()
    campaign = get_campaign_or_404(db, slug)
    if campaign.status != CampaignStatus.active:
        raise HTTPException(400, "This campaign is not open for participation")
    roles = campaign_roles(db, campaign, user)
    if MemberRole.participant not in roles:
        if (MemberRole.jury in roles
                and not campaign.effective_settings.get("jury_can_submit")):
            raise HTTPException(
                403, "Jury members cannot participate in this campaign")
        db.add(CampaignMember(campaign_id=campaign.id, user_id=user.id,
                              role=MemberRole.participant, added_by=user.id))
        audit(db, user, "join", "campaign", campaign.id, {"slug": slug})
        db.commit()
        db.refresh(campaign)
    return respond(campaign_detail_out(db, campaign, user))


@bp.get("/campaigns/<slug>/suggested-links")
def suggested_links(slug: str):
    """Suggested Wikidata items resolved to per-language wikilinks via
    their sitelinks. Languages: ?languages=ml,ta — else the logged-in
    user's preferred languages — else the campaign's language.
    Optional ?qids=Q1,Q2 restricts which suggested items are resolved
    (e.g. just the active heading tab), so adding a language to a large
    suggested list doesn't refetch sitelinks for every item every time."""
    db, user = get_db(), get_current_user()
    campaign = get_campaign_or_404(db, slug)
    raw = request.args.get("languages", "")
    langs = [code for code in (s.strip().lower() for s in raw.split(",")) if code]
    if not langs and user is not None:
        langs = [code for code in (user.preferred_languages or "").split(",")
                 if code]
    if not langs:
        langs = [campaign.language]
    langs = langs[:10]
    # English always rides along: the suggested-items table shows an
    # English column and English labels next to the user's languages.
    if "en" not in langs:
        langs.append("en")
    suggested = [p for p in campaign.suggested_pages
                 if p.kind == SubmissionKind.wikidata_item]
    qid_filter = request.args.get("qids", "")
    if qid_filter:
        wanted = {q.strip().upper() for q in qid_filter.split(",") if q.strip()}
        suggested = [p for p in suggested if p.title.upper() in wanted]
    qids = [p.title for p in suggested]
    try:
        entities = mediawiki.fetch_sitelinks(qids, langs)
    except Exception:
        raise HTTPException(502, "Could not reach Wikidata for sitelinks")
    items = []
    for page in suggested:
        qid = page.title
        entity = entities.get(qid) or {"label": None, "label_en": None,
                                       "links": {}}
        items.append({
            "qid": qid,
            "section": page.section or "",
            "label": entity["label"],
            "label_en": entity.get("label_en"),
            "links": [
                {"lang": lang, "title": entity["links"][lang],
                 "url": (f"https://{lang}.wikipedia.org/wiki/"
                         + entity["links"][lang].replace(" ", "_"))}
                for lang in langs if lang in entity["links"]
            ],
        })
    return respond({"languages": langs, "items": items})


@bp.post("/campaigns/<slug>/members")
def add_member(slug: str):
    """Organizer/admin: add a user to the campaign with a role
    (participant, jury or organizer). Creates the user if needed."""
    db, user = get_db(), require_user()
    payload = parse(MemberAddIn)
    campaign = get_campaign_or_404(db, slug)
    require_organizer(db, campaign, user)
    member_user = get_or_create_user(db, payload.username)
    exists = db.query(CampaignMember).filter_by(
        campaign_id=campaign.id, user_id=member_user.id,
        role=payload.role).first()
    if exists:
        raise HTTPException(
            409, f"{member_user.username} already has the "
                 f"{payload.role.value} role in this campaign")
    db.add(CampaignMember(campaign_id=campaign.id, user_id=member_user.id,
                          role=payload.role, added_by=user.id))
    audit(db, user, "add_member", "campaign", campaign.id,
          {"slug": slug, "username": member_user.username,
           "role": payload.role.value})
    db.commit()
    db.refresh(campaign)
    return respond(campaign_detail_out(db, campaign, user), 201)


@bp.delete("/campaigns/<slug>/members/<int:member_id>")
def remove_member(slug: str, member_id: int):
    """Organizer/admin: remove a role from a campaign member."""
    db, user = get_db(), require_user()
    campaign = get_campaign_or_404(db, slug)
    require_organizer(db, campaign, user)
    member = db.get(CampaignMember, member_id)
    if member is None or member.campaign_id != campaign.id:
        raise HTTPException(404, "Member not found")
    if member.role == MemberRole.organizer:
        organizers = [m for m in campaign.members
                      if m.role == MemberRole.organizer]
        if len(organizers) <= 1:
            raise HTTPException(400, "A campaign needs at least one organizer")
    audit(db, user, "remove_member", "campaign", campaign.id,
          {"slug": slug, "username": member.user.username,
           "role": member.role.value})
    db.delete(member)
    db.commit()
    db.refresh(campaign)
    return respond(campaign_detail_out(db, campaign, user))


@bp.get("/campaigns/<slug>/approval-rights")
def approval_rights(slug: str):
    """Whether the current user may approve this campaign, and why (not)."""
    db, user = get_db(), get_current_user()
    campaign = get_campaign_or_404(db, slug)
    if user is None:
        return respond({"can_approve": False, "reason": "not_logged_in"})
    allowed, reason = wiki_rights.can_approve_campaign(user, campaign)
    return respond({"can_approve": allowed, "reason": reason,
                    "wiki_domain": campaign.wiki_domain,
                    "scoring_mode": campaign.scoring_mode.value})


def _require_approval_rights(campaign: Campaign, user: User) -> str:
    allowed, reason = wiki_rights.can_approve_campaign(user, campaign)
    if not allowed:
        need = (f"an admin (sysop) on {campaign.wiki_domain}"
                if campaign.scoring_mode == ScoringMode.jury
                else "an admin (sysop) on any Wikipedia project")
        raise HTTPException(
            403, f"Approving this campaign requires {need} ({reason})")
    return reason


@bp.post("/campaigns/<slug>/approve")
def approve_campaign(slug: str):
    db, user = get_db(), require_user()
    campaign = get_campaign_or_404(db, slug)
    reason = _require_approval_rights(campaign, user)
    if campaign.status not in (CampaignStatus.draft, CampaignStatus.rejected):
        raise HTTPException(400, f"Campaign is already {campaign.status.value}")
    campaign.status = CampaignStatus.active
    audit(db, user, "approve", "campaign", campaign.id,
          {"slug": slug, "approved_by_right": reason})
    db.commit()
    db.refresh(campaign)
    return respond(campaign_detail_out(db, campaign, user))


@bp.post("/campaigns/<slug>/deactivate")
def deactivate_campaign(slug: str):
    """Organizer/admin: take an active campaign offline (back to draft).
    Reactivating goes through the approval flow again."""
    db, user = get_db(), require_user()
    campaign = get_campaign_or_404(db, slug)
    require_organizer(db, campaign, user)
    if campaign.status != CampaignStatus.active:
        raise HTTPException(400, "Only active campaigns can be deactivated")
    campaign.status = CampaignStatus.draft
    audit(db, user, "deactivate", "campaign", campaign.id, {"slug": slug})
    db.commit()
    db.refresh(campaign)
    return respond(campaign_detail_out(db, campaign, user))


@bp.post("/campaigns/<slug>/reject")
def reject_campaign(slug: str):
    db, user = get_db(), require_user()
    campaign = get_campaign_or_404(db, slug)
    _require_approval_rights(campaign, user)
    reason = (request.get_json(silent=True) or {}).get("reason", "")
    campaign.status = CampaignStatus.rejected
    audit(db, user, "reject", "campaign", campaign.id,
          {"slug": slug, "reason": reason})
    db.commit()
    db.refresh(campaign)
    return respond(campaign_detail_out(db, campaign, user))


@bp.get("/campaigns/<slug>/leaderboard")
def leaderboard(slug: str):
    db, user = get_db(), get_current_user()
    campaign = get_campaign_or_404(db, slug)
    if not campaign.effective_settings.get("show_leaderboard", True):
        allowed = user and (user.is_admin or campaign_roles(db, campaign, user)
                            & {MemberRole.organizer, MemberRole.jury})
        if not allowed:
            raise HTTPException(403, "The leaderboard is not public")
    return respond(compute_leaderboard(db, campaign))


@bp.get("/campaigns/<slug>/participants/<int:user_id>/details")
def participant_details(slug: str, user_id: int):
    """Live per-submission facts for one participant (leaderboard popup).
    Details are fetched from the MediaWiki APIs on demand; a failed fetch
    marks the submission instead of failing the whole response."""
    db, user = get_db(), get_current_user()
    campaign = get_campaign_or_404(db, slug)
    if not can_see_campaign(db, campaign, user):
        raise HTTPException(404, "Campaign not found")
    if not campaign.effective_settings.get("show_leaderboard", True):
        allowed = user and (user.is_admin or campaign_roles(db, campaign, user)
                            & {MemberRole.organizer, MemberRole.jury})
        if not allowed:
            raise HTTPException(403, "The leaderboard is not public")

    settings = campaign.effective_settings
    subs = [s for s in load_submissions(db, campaign.id)
            if s.user_id == user_id]

    def fetch_details(kind: SubmissionKind, wiki_domain: str, title: str,
                      metrics) -> tuple[dict | None, bool]:
        try:
            if kind == SubmissionKind.article:
                return mediawiki.fetch_article_details(wiki_domain, title), False
            if kind == SubmissionKind.wikidata_item:
                return mediawiki.fetch_wikidata_details(title), False
            if kind == SubmissionKind.commons_file:
                return mediawiki.fetch_commons_details(title), False
            # Bulk kinds: the stored activity counts are the details.
            return metrics, False
        except Exception:
            return None, True

    # Each article/item costs 1–2 wiki round-trips; fetched concurrently
    # rather than serially, so the popup arrives in roughly one fetch's
    # time instead of submissions × round-trips. Only plain values cross
    # the thread boundary — no ORM objects, no db session.
    args = [(s.kind, s.wiki_domain, s.title, s.metrics) for s in subs]
    with ThreadPoolExecutor(max_workers=min(8, len(subs) or 1)) as pool:
        fetched = list(pool.map(lambda a: fetch_details(*a), args))

    out = []
    for sub, (details, failed) in zip(subs, fetched):
        bd = compute_breakdown(sub, campaign.rules,
                               suggested_titles(campaign, sub.kind),
                               campaign.scoring_mode, settings)
        out.append({
            "id": sub.id, "kind": sub.kind, "title": sub.title,
            "url": sub.url, "wiki_domain": sub.wiki_domain,
            "status": sub.status, "points": bd.total,
            "submitted_at": sub.submitted_at, "details": details,
            "fetch_failed": failed,
        })
    return respond(out)


@bp.get("/campaigns/<slug>/stats")
def campaign_stats(slug: str):
    db, user = get_db(), get_current_user()
    campaign = get_campaign_or_404(db, slug)
    if not can_see_campaign(db, campaign, user):
        raise HTTPException(404, "Campaign not found")
    settings = campaign.effective_settings
    subs = load_submissions(db, campaign.id)

    timeline = Counter(s.submitted_at.date().isoformat() for s in subs)
    # Language is the Wikipedia subdomain prefix, only meaningful for
    # article submissions (Wikidata/Commons/bulk kinds aren't a language).
    by_language = Counter(
        s.wiki_domain.split(".")[0] for s in subs
        if s.kind == SubmissionKind.article)
    total_points = 0.0
    reviews = claims = pending_claims = unreviewed = 0
    for sub in subs:
        reviews += len(sub.reviews)
        claims += len(sub.claims)
        pending_claims += sum(1 for c in sub.claims
                              if c.status.value == "claimed")
        if not sub.reviews and not sub.claims:
            unreviewed += 1
        if sub.status.value != "rejected":
            bd = compute_breakdown(sub, campaign.rules,
                                   suggested_titles(campaign, sub.kind),
                                   campaign.scoring_mode, settings)
            total_points = round(total_points + bd.total, 2)

    return respond(CampaignStats(
        submissions=len(subs),
        participants=len({s.user_id for s in subs}),
        languages=len(by_language),
        reviews=reviews,
        claims=claims,
        pending_claims=pending_claims,
        unreviewed_submissions=unreviewed,
        total_points=total_points,
        total_bytes_added=sum(s.bytes_added or 0 for s in subs),
        new_pages=sum(1 for s in subs if s.is_new_page),
        by_kind=dict(Counter(s.kind.value for s in subs)),
        by_status=dict(Counter(s.status.value for s in subs)),
        by_language=dict(by_language),
        timeline=[{"date": d, "submissions": n}
                  for d, n in sorted(timeline.items())],
        top_contributors=compute_leaderboard(db, campaign, subs)[:10],
    ))

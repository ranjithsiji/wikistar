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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import settings_registry
from auth import (
    campaign_roles,
    get_current_user,
    require_admin,
    require_organizer,
    require_user,
)
from db import get_db
from models import (
    Campaign,
    CampaignMember,
    CampaignStatus,
    MemberRole,
    ScoringRule,
    SubmissionKind,
    SuggestedPage,
    User,
)
from routers.common import (
    audit,
    campaign_detail_out,
    campaign_summary,
    can_see_campaign,
    compute_leaderboard,
    get_campaign_or_404,
    get_or_create_user,
    load_submissions,
    slugify,
    suggested_titles,
    unique_slug,
)
from schemas import (
    CampaignDetail,
    CampaignIn,
    CampaignStats,
    CampaignSummary,
    LeaderboardRow,
)
from scoring import compute_breakdown, default_self_assessment_rules

router = APIRouter(prefix="/api", tags=["campaigns"])


@router.get("/meta")
def meta():
    """Static metadata the frontend needs to render forms."""
    return {
        "settings_registry": settings_registry.SETTING_DEFS,
        "default_rules": {"self": default_self_assessment_rules()},
        "scoring_modes": ["jury", "self", "hybrid"],
    }


@router.get("/campaigns", response_model=list[CampaignSummary])
def list_campaigns(db: Session = Depends(get_db),
                   user: User | None = Depends(get_current_user)):
    campaigns = db.query(Campaign).order_by(Campaign.start_date.desc()).all()
    return [campaign_summary(c) for c in campaigns
            if can_see_campaign(db, c, user)]


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


def _replace_suggested(campaign: Campaign, payload: CampaignIn) -> None:
    campaign.suggested_pages = (
        [SuggestedPage(kind=SubmissionKind.article, title=t.strip())
         for t in dict.fromkeys(payload.suggested_articles) if t.strip()]
        + [SuggestedPage(kind=SubmissionKind.wikidata_item, title=t.strip())
           for t in dict.fromkeys(payload.suggested_items) if t.strip()]
    )


def _replace_rules(db: Session, campaign: Campaign, payload: CampaignIn) -> None:
    """Upsert rules by id. Removed rules are deleted unless claims
    reference them, in which case they are deactivated to keep history."""
    from models import Claim

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


@router.post("/campaigns", response_model=CampaignDetail, status_code=201)
def create_campaign(payload: CampaignIn, db: Session = Depends(get_db),
                    user: User = Depends(require_user)):
    overrides = _validated_settings(payload)
    slug = unique_slug(db, payload.slug or slugify(payload.name))
    campaign = Campaign(slug=slug, status=CampaignStatus.draft,
                        created_by=user.id)
    _apply_scalar_fields(campaign, payload)
    db.add(campaign)
    db.flush()
    campaign.set_settings(overrides)
    db.add(CampaignMember(campaign_id=campaign.id, user_id=user.id,
                          role=MemberRole.organizer, added_by=user.id))
    _replace_jury(db, campaign, payload.jury_usernames, user)
    _replace_suggested(campaign, payload)
    _replace_rules(db, campaign, payload)
    audit(db, user, "create", "campaign", campaign.id,
          {"slug": slug, "name": campaign.name})
    db.commit()
    db.refresh(campaign)
    return campaign_detail_out(db, campaign, user)


@router.get("/campaigns/{slug}", response_model=CampaignDetail)
def campaign_detail(slug: str, db: Session = Depends(get_db),
                    user: User | None = Depends(get_current_user)):
    campaign = get_campaign_or_404(db, slug)
    if not can_see_campaign(db, campaign, user):
        raise HTTPException(404, "Campaign not found")
    return campaign_detail_out(db, campaign, user)


# Transitions organizers may perform themselves; admins may do anything.
ORGANIZER_TRANSITIONS = {
    (CampaignStatus.active, CampaignStatus.finished),
    (CampaignStatus.finished, CampaignStatus.active),
    (CampaignStatus.finished, CampaignStatus.archived),
}


@router.put("/campaigns/{slug}", response_model=CampaignDetail)
def update_campaign(slug: str, payload: CampaignIn,
                    db: Session = Depends(get_db),
                    user: User = Depends(require_user)):
    campaign = get_campaign_or_404(db, slug)
    require_organizer(db, campaign, user)
    overrides = _validated_settings(payload)

    if payload.slug and payload.slug != campaign.slug:
        campaign.slug = unique_slug(db, payload.slug, exclude_id=campaign.id)
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
    _replace_jury(db, campaign, payload.jury_usernames, user)
    _replace_suggested(campaign, payload)
    _replace_rules(db, campaign, payload)
    audit(db, user, "update", "campaign", campaign.id, {"slug": campaign.slug})
    db.commit()
    db.refresh(campaign)
    return campaign_detail_out(db, campaign, user)


@router.delete("/campaigns/{slug}", status_code=204)
def delete_campaign(slug: str, db: Session = Depends(get_db),
                    user: User = Depends(require_user)):
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


@router.post("/campaigns/{slug}/join", response_model=CampaignDetail)
def join_campaign(slug: str, db: Session = Depends(get_db),
                  user: User = Depends(require_user)):
    """Join as a participant — works the same in jury and self modes."""
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
    return campaign_detail_out(db, campaign, user)


@router.post("/campaigns/{slug}/approve", response_model=CampaignDetail)
def approve_campaign(slug: str, db: Session = Depends(get_db),
                     user: User = Depends(require_admin)):
    campaign = get_campaign_or_404(db, slug)
    if campaign.status not in (CampaignStatus.draft, CampaignStatus.rejected):
        raise HTTPException(400, f"Campaign is already {campaign.status.value}")
    campaign.status = CampaignStatus.active
    audit(db, user, "approve", "campaign", campaign.id, {"slug": slug})
    db.commit()
    db.refresh(campaign)
    return campaign_detail_out(db, campaign, user)


@router.post("/campaigns/{slug}/reject", response_model=CampaignDetail)
def reject_campaign(slug: str, payload: dict | None = None,
                    db: Session = Depends(get_db),
                    user: User = Depends(require_admin)):
    campaign = get_campaign_or_404(db, slug)
    reason = (payload or {}).get("reason", "")
    campaign.status = CampaignStatus.rejected
    audit(db, user, "reject", "campaign", campaign.id,
          {"slug": slug, "reason": reason})
    db.commit()
    db.refresh(campaign)
    return campaign_detail_out(db, campaign, user)


@router.get("/campaigns/{slug}/leaderboard",
            response_model=list[LeaderboardRow])
def leaderboard(slug: str, db: Session = Depends(get_db),
                user: User | None = Depends(get_current_user)):
    campaign = get_campaign_or_404(db, slug)
    if not campaign.effective_settings.get("show_leaderboard", True):
        allowed = user and (user.is_admin or campaign_roles(db, campaign, user)
                            & {MemberRole.organizer, MemberRole.jury})
        if not allowed:
            raise HTTPException(403, "The leaderboard is not public")
    return compute_leaderboard(db, campaign)


@router.get("/campaigns/{slug}/stats", response_model=CampaignStats)
def campaign_stats(slug: str, db: Session = Depends(get_db),
                   user: User | None = Depends(get_current_user)):
    campaign = get_campaign_or_404(db, slug)
    if not can_see_campaign(db, campaign, user):
        raise HTTPException(404, "Campaign not found")
    settings = campaign.effective_settings
    subs = load_submissions(db, campaign.id)

    timeline = Counter(s.submitted_at.date().isoformat() for s in subs)
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

    return CampaignStats(
        submissions=len(subs),
        participants=len({s.user_id for s in subs}),
        reviews=reviews,
        claims=claims,
        pending_claims=pending_claims,
        unreviewed_submissions=unreviewed,
        total_points=total_points,
        total_bytes_added=sum(s.bytes_added or 0 for s in subs),
        new_pages=sum(1 for s in subs if s.is_new_page),
        by_kind=dict(Counter(s.kind.value for s in subs)),
        by_status=dict(Counter(s.status.value for s in subs)),
        timeline=[{"date": d, "submissions": n}
                  for d, n in sorted(timeline.items())],
        top_contributors=compute_leaderboard(db, campaign)[:10],
    )

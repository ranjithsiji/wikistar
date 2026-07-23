"""Helpers shared by the routers: lookups, serializers, audit logging."""
import re

from sqlalchemy.orm import Session, selectinload

from webutil import HTTPException

from models import (
    AuditLog,
    Campaign,
    CampaignStatus,
    MemberRole,
    Submission,
    SubmissionKind,
    User,
)
from schemas import (
    CampaignDetail,
    CampaignSummary,
    LeaderboardRow,
    MemberOut,
    PointLineOut,
    RuleOut,
    SubmissionOut,
    SuggestedItemOut,
    UserOut,
)
from scoring import compute_breakdown


def audit(db: Session, user: User | None, action: str,
          entity_type: str | None = None, entity_id: int | None = None,
          details: dict | None = None) -> None:
    db.add(AuditLog(user_id=user.id if user else None, action=action,
                    entity_type=entity_type, entity_id=entity_id,
                    details=details))


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9_-]+", "-", text.lower()).strip("-")
    return slug or "campaign"


def unique_slug(db: Session, base: str, exclude_id: int | None = None) -> str:
    slug, suffix = base, 1
    while True:
        q = db.query(Campaign.id).filter_by(slug=slug)
        if exclude_id is not None:
            q = q.filter(Campaign.id != exclude_id)
        if q.first() is None:
            return slug
        suffix += 1
        slug = f"{base}-{suffix}"


def get_campaign_or_404(db: Session, slug: str) -> Campaign:
    campaign = db.query(Campaign).filter_by(slug=slug).first()
    if campaign is None:
        raise HTTPException(404, "Campaign not found")
    return campaign


def get_or_create_user(db: Session, username: str) -> User:
    username = username.strip()
    user = db.query(User).filter_by(username=username).first()
    if user is None:
        user = User(username=username)
        db.add(user)
        db.flush()
    return user


def suggested_titles(campaign: Campaign, kind: SubmissionKind) -> set[str]:
    """Keys a submission of `kind` can match for the suggested-list bonus:
    the suggested titles of that kind, plus — for articles — the suggested
    Wikidata item QIDs, so an article that is a suggested item's sitelink
    also matches (scoring compares the article's connected QID)."""
    keys = {p.title.lower() for p in campaign.suggested_pages if p.kind == kind}
    if kind == SubmissionKind.article:
        keys |= {p.title.upper() for p in campaign.suggested_pages
                 if p.kind == SubmissionKind.wikidata_item}
    return keys


def load_submissions(db: Session, campaign_id: int) -> list[Submission]:
    return (
        db.query(Submission)
        .filter_by(campaign_id=campaign_id)
        .options(
            selectinload(Submission.user),
            selectinload(Submission.reviews),
            selectinload(Submission.claims),
        )
        .order_by(Submission.submitted_at.desc())
        .all()
    )


def submission_out(campaign: Campaign, sub: Submission,
                   settings: dict | None = None) -> SubmissionOut:
    settings = settings if settings is not None else campaign.effective_settings
    bd = compute_breakdown(sub, campaign.rules,
                           suggested_titles(campaign, sub.kind),
                           campaign.scoring_mode, settings)
    out = SubmissionOut.model_validate(sub)
    out.points = bd.total
    out.breakdown = [PointLineOut(**vars(line)) for line in bd.lines]
    return out


def campaign_counts(campaign: Campaign) -> dict:
    subs = campaign.submissions
    return dict(
        submission_count=len(subs),
        participant_count=len({s.user_id for s in subs}),
        review_count=sum(len(s.reviews) for s in subs),
    )


def campaign_summary(campaign: Campaign) -> CampaignSummary:
    out = CampaignSummary.model_validate(campaign)
    for key, value in campaign_counts(campaign).items():
        setattr(out, key, value)
    return out


def campaign_detail_out(db: Session, campaign: Campaign,
                        user: User | None) -> CampaignDetail:
    from auth import campaign_roles  # local import to avoid cycle at startup

    out = CampaignDetail.model_validate(campaign)
    for key, value in campaign_counts(campaign).items():
        setattr(out, key, value)
    out.settings = campaign.effective_settings
    out.created_by_username = campaign.creator.username if campaign.creator else None
    out.rules = [RuleOut.model_validate(r) for r in campaign.rules if r.active]
    out.members = [MemberOut.model_validate(m) for m in campaign.members]
    out.suggested_articles = [p.title for p in campaign.suggested_pages
                              if p.kind == SubmissionKind.article]
    out.suggested_items = [
        SuggestedItemOut(qid=p.title, section=p.section or "")
        for p in campaign.suggested_pages
        if p.kind == SubmissionKind.wikidata_item]
    out.my_roles = sorted(campaign_roles(db, campaign, user), key=lambda r: r.value)
    return out


def can_see_campaign(db: Session, campaign: Campaign, user: User | None) -> bool:
    if campaign.status not in (CampaignStatus.draft, CampaignStatus.rejected):
        return True
    if user is None:
        return False
    if user.is_admin or campaign.created_by == user.id:
        return True
    from auth import campaign_roles

    if MemberRole.organizer in campaign_roles(db, campaign, user):
        return True
    # Drafts awaiting approval are visible to whoever could approve them
    # (jury: the target wiki's sysops; multi-language/self: any sysop).
    if campaign.status == CampaignStatus.draft:
        import wiki_rights

        return wiki_rights.can_approve_campaign(user, campaign)[0]
    return False


def compute_leaderboard(db: Session, campaign: Campaign) -> list[LeaderboardRow]:
    settings = campaign.effective_settings
    totals: dict[int, dict] = {}
    for sub in load_submissions(db, campaign.id):
        if sub.status.value == "rejected":
            continue
        bd = compute_breakdown(sub, campaign.rules,
                               suggested_titles(campaign, sub.kind),
                               campaign.scoring_mode, settings)
        entry = totals.setdefault(
            sub.user_id, {"user": sub.user, "submission_count": 0,
                         "points": 0.0, "bytes_added": 0})
        entry["submission_count"] += 1
        entry["points"] = round(entry["points"] + bd.total, 2)
        entry["bytes_added"] += sub.bytes_added or 0
    ranked = sorted(totals.values(), key=lambda e: -e["points"])
    rows: list[LeaderboardRow] = []
    for i, e in enumerate(ranked):
        # Fountain-style ranking: equal totals share a rank.
        rank = (rows[-1].rank if rows and rows[-1].points == e["points"]
                else i + 1)
        rows.append(LeaderboardRow(
            rank=rank, user=UserOut.model_validate(e["user"]),
            submission_count=e["submission_count"], points=e["points"],
            bytes_added=e["bytes_added"]))
    return rows

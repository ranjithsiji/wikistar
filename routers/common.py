"""Helpers shared by the routers: lookups, serializers, audit logging."""

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from core.webutil import HTTPException

from domain.models import (
    AuditLog,
    Campaign,
    CampaignStatus,
    MemberRole,
    Review,
    Submission,
    SubmissionKind,
    User,
)
from domain.schemas import (
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
from domain.scoring import compute_breakdown, normalize_title


def audit(db: Session, user: User | None, action: str,
          entity_type: str | None = None, entity_id: int | None = None,
          details: dict | None = None) -> None:
    db.add(AuditLog(user_id=user.id if user else None, action=action,
                    entity_type=entity_type, entity_id=entity_id,
                    details=details))


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
    """Keys a submission of `kind` can match for the suggested-list bonus.

    Articles are matched by Wikidata QID only: the item is what identifies
    a subject across spellings and language editions, so a title that
    merely looks right is not enough. The key set therefore holds the QIDs
    of suggested items plus the items resolved from suggested articles.
    (Wikidata item submissions match on their own title, which *is* a QID.)
    """
    if kind != SubmissionKind.article:
        return {normalize_title(p.title) for p in campaign.suggested_pages
                if p.kind == kind}
    keys = {p.title.strip().upper() for p in campaign.suggested_pages
            if p.kind == SubmissionKind.wikidata_item}
    keys |= {p.qid.strip().upper() for p in campaign.suggested_pages
             if p.kind == SubmissionKind.article and p.qid}
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


def campaign_counts(db: Session, campaigns: list[Campaign]) -> dict[int, dict]:
    """Submission / participant / review counts for many campaigns at
    once, in two grouped aggregate queries. Counting through the ORM
    relationships instead would hydrate every submission row and then
    lazy-load each submission's reviews — campaigns × (1 + submissions)
    queries on a campaign list page."""
    counts = {c.id: dict(submission_count=0, participant_count=0,
                         review_count=0)
              for c in campaigns}
    if not counts:
        return counts
    ids = list(counts)
    rows = (db.query(Submission.campaign_id,
                     func.count(Submission.id),
                     func.count(func.distinct(Submission.user_id)))
            .filter(Submission.campaign_id.in_(ids))
            .group_by(Submission.campaign_id))
    for cid, sub_count, user_count in rows:
        counts[cid].update(submission_count=sub_count,
                           participant_count=user_count)
    rows = (db.query(Submission.campaign_id, func.count(Review.id))
            .join(Review, Review.submission_id == Submission.id)
            .filter(Submission.campaign_id.in_(ids))
            .group_by(Submission.campaign_id))
    for cid, review_count in rows:
        counts[cid]["review_count"] = review_count
    return counts


def campaign_summary(db: Session, campaign: Campaign,
                     counts: dict | None = None) -> CampaignSummary:
    """One campaign's summary card. For lists, precompute `counts` for
    all campaigns with campaign_counts() and pass each campaign's entry."""
    out = CampaignSummary.model_validate(campaign)
    if counts is None:
        counts = campaign_counts(db, [campaign])[campaign.id]
    for key, value in counts.items():
        setattr(out, key, value)
    return out


def campaign_detail_out(db: Session, campaign: Campaign,
                        user: User | None) -> CampaignDetail:
    from auth import campaign_roles  # local import to avoid cycle at startup

    out = CampaignDetail.model_validate(campaign)
    for key, value in campaign_counts(db, [campaign])[campaign.id].items():
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
        from integrations import wiki_rights

        return wiki_rights.can_approve_campaign(user, campaign)[0]
    return False


def compute_leaderboard(db: Session, campaign: Campaign,
                        subs: list[Submission] | None = None
                        ) -> list[LeaderboardRow]:
    """Pass `subs` when the caller already holds the campaign's loaded
    submissions (e.g. the stats endpoint) — they are the heaviest thing
    this loads, and reloading them doubled that endpoint's DB work."""
    settings = campaign.effective_settings
    totals: dict[int, dict] = {}
    if subs is None:
        subs = load_submissions(db, campaign.id)
    for sub in subs:
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

"""Helpers shared by the routers: lookups, serializers, audit logging,
and the cached-points bookkeeping (rescore_* / ensure_scored)."""
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from core.webutil import HTTPException

from domain.models import (
    AuditLog,
    Campaign,
    CampaignMember,
    CampaignStatus,
    MemberRole,
    Review,
    Submission,
    SubmissionKind,
    SubmissionStatus,
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
            # The reviewer rides along: serializing a review names its
            # reviewer, and without this every review row costs its own
            # SELECT — thousands of round-trips on a large campaign.
            selectinload(Submission.reviews).selectinload(Review.reviewer),
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
    # Loaded with their users in one go: serializing a member names its
    # user, and iterating campaign.members would lazy-load one user per
    # row — hundreds of SELECTs for a campaign with many participants.
    members = (db.query(CampaignMember)
               .options(selectinload(CampaignMember.user))
               .filter_by(campaign_id=campaign.id).all())
    out.members = [MemberOut.model_validate(m) for m in members]
    out.suggested_articles = [p.title for p in campaign.suggested_pages
                              if p.kind == SubmissionKind.article]
    out.suggested_items = [
        SuggestedItemOut(qid=p.title, section=p.section or "")
        for p in campaign.suggested_pages
        if p.kind == SubmissionKind.wikidata_item]
    out.my_roles = sorted(campaign_roles(db, campaign, user), key=lambda r: r.value)
    return out


def can_see_campaign(db: Session, campaign: Campaign, user: User | None,
                     check_rights: bool = True) -> bool:
    """Whether `user` may see this campaign.

    check_rights=False skips the on-wiki sysop lookup that decides
    whether a non-organizer may see a *draft*. Callers filtering a long
    list use it to avoid a blocking API call per draft row; see
    visible_campaigns, which resolves the rights once for the whole list.
    """
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
    if campaign.status == CampaignStatus.draft and check_rights:
        from integrations import wiki_rights

        return wiki_rights.can_approve_campaign(user, campaign)[0]
    return False


def visible_campaigns(db: Session, campaigns: list[Campaign],
                      user: User | None) -> list[Campaign]:
    """Filter a campaign list to what `user` may see.

    The sysop-rights lookup that reveals other people's drafts hits the
    CentralAuth API, so it is done only if a draft actually survives the
    cheap checks — and its one result is reused for every remaining
    draft, instead of a blocking call per row.
    """
    decided: dict[int, bool] = {}
    undecided: list[Campaign] = []
    for c in campaigns:
        if can_see_campaign(db, c, user, check_rights=False):
            decided[c.id] = True
        elif c.status == CampaignStatus.draft and user is not None:
            undecided.append(c)
    if undecided:
        from integrations import wiki_rights

        # can_approve_campaign consults the campaign's own scoring mode
        # and target wiki, but resolves the user's rights through a
        # process-wide cache — so this is one API call per request at
        # worst, not one per draft.
        for c in undecided:
            decided[c.id] = wiki_rights.can_approve_campaign(user, c)[0]
    return [c for c in campaigns if decided.get(c.id)]


# ---- cached points ---------------------------------------------------------
# Points are a function of the submission, its reviews/claims and the
# campaign's rules/settings. The scoring engine stays the single source
# of truth, but its result is written to Submission.points_cached by the
# handful of writes that can change it — so every read path (lists,
# leaderboard, statistics) is plain SQL over that column instead of a
# campaign-wide rescore per request.

def rescore_submission(campaign: Campaign, sub: Submission,
                       settings: dict | None = None) -> None:
    """Refresh one submission's cached points. Call from any write that
    changes this submission's score inputs (review, claim, moderation,
    metadata refresh) — after flushing, so relationship collections see
    the write."""
    settings = settings if settings is not None else campaign.effective_settings
    bd = compute_breakdown(sub, campaign.rules,
                           suggested_titles(campaign, sub.kind),
                           campaign.scoring_mode, settings)
    sub.points_cached = bd.total


def rescore_campaign(db: Session, campaign: Campaign) -> None:
    """Refresh every submission's cached points — for writes with
    campaign-wide effect (rule / settings / suggested-list edits) and
    the lazy backfill of rows from before the cache existed."""
    settings = campaign.effective_settings
    keys_by_kind: dict[SubmissionKind, set[str]] = {}
    for sub in load_submissions(db, campaign.id):
        keys = keys_by_kind.get(sub.kind)
        if keys is None:
            keys = keys_by_kind[sub.kind] = suggested_titles(campaign, sub.kind)
        bd = compute_breakdown(sub, campaign.rules, keys,
                               campaign.scoring_mode, settings)
        sub.points_cached = bd.total


def ensure_scored(db: Session, campaign: Campaign) -> None:
    """Backfill points_cached lazily: rows from before the column existed
    are NULL, so the first read of such a campaign rescored it once and
    commits; afterwards this is a single indexed EXISTS check."""
    missing = (db.query(Submission.id)
               .filter(Submission.campaign_id == campaign.id,
                       Submission.points_cached.is_(None))
               .first())
    if missing:
        rescore_campaign(db, campaign)
        db.commit()


def compute_leaderboard(db: Session,
                        campaign: Campaign) -> list[LeaderboardRow]:
    """Standings from the cached points: one grouped query (with a
    review-coverage subquery) instead of loading and rescoring every
    submission. Rejected submissions never count, same as before."""
    ensure_scored(db, campaign)
    reviewed = (
        db.query(Review.submission_id)
        .join(Submission, Review.submission_id == Submission.id)
        .filter(Submission.campaign_id == campaign.id)
        .distinct().subquery())
    rows = (
        db.query(
            User,
            func.count(Submission.id),
            func.coalesce(func.sum(Submission.points_cached), 0),
            func.coalesce(func.sum(Submission.bytes_added), 0),
            func.count(reviewed.c.submission_id))
        .join(Submission, Submission.user_id == User.id)
        .outerjoin(reviewed, reviewed.c.submission_id == Submission.id)
        .filter(Submission.campaign_id == campaign.id,
                Submission.status != SubmissionStatus.rejected)
        .group_by(User.id)
        .all())
    ranked = sorted(
        ((user, count, round(float(points or 0), 2), int(bytes_ or 0),
          reviewed_count)
         for user, count, points, bytes_, reviewed_count in rows),
        key=lambda r: -r[2])
    out: list[LeaderboardRow] = []
    for i, (user, count, points, bytes_, reviewed_count) in enumerate(ranked):
        # Fountain-style ranking: equal totals share a rank.
        rank = (out[-1].rank if out and out[-1].points == points else i + 1)
        out.append(LeaderboardRow(
            rank=rank, user=UserOut.model_validate(user),
            submission_count=count, points=points, bytes_added=bytes_,
            reviewed_count=reviewed_count))
    return out

"""Site administration: stats, audit log, user and submission control."""
import re

from flask import Blueprint, request
from sqlalchemy import desc, func

from integrations import mediawiki
from auth import require_admin
from core.db import get_db
from core.webutil import HTTPException, jsonable, respond
from domain.models import (AuditLog, Campaign, CampaignStatus, Claim, Review,
                           Submission, SubmissionKind, User)
from routers.common import (audit, campaign_counts, campaign_summary,
                            submission_out)

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.before_request
def _gate():
    require_admin()


@bp.get("/campaigns")
def campaigns():
    """Every campaign regardless of status, for the admin editathon list."""
    db = get_db()
    rows = db.query(Campaign).order_by(Campaign.start_date.desc()).all()
    counts = campaign_counts(db, rows)
    out = []
    for c in rows:
        summary = jsonable(campaign_summary(db, c, counts[c.id]))
        summary["created_by_username"] = c.creator.username if c.creator else None
        out.append(summary)
    return respond(out)


@bp.get("/stats")
def stats():
    db = get_db()
    count = lambda q: q.scalar() or 0  # noqa: E731
    return respond({
        "users": count(db.query(func.count(User.id))),
        "campaigns": count(db.query(func.count(Campaign.id))),
        "active_campaigns": count(db.query(func.count(Campaign.id))
            .filter(Campaign.status == CampaignStatus.active)),
        "pending_campaigns": count(db.query(func.count(Campaign.id))
            .filter(Campaign.status == CampaignStatus.draft)),
        "submissions": count(db.query(func.count(Submission.id))),
        "reviews": count(db.query(func.count(Review.id))),
        "claims": count(db.query(func.count(Claim.id))),
    })


@bp.get("/logs")
def logs():
    db = get_db()
    limit = min(max(request.args.get("limit", 50, type=int), 1), 200)
    offset = request.args.get("offset", 0, type=int)
    query = (db.query(AuditLog, User.username)
             .outerjoin(User, AuditLog.user_id == User.id))
    action = (request.args.get("action") or "").strip()
    if action:
        query = query.filter(AuditLog.action == action)
    username = (request.args.get("username") or "").strip()
    if username:
        query = query.filter(User.username.ilike(f"%{username}%"))
    total = query.count()
    rows = (query.order_by(desc(AuditLog.created_at), desc(AuditLog.id))
            .limit(limit).offset(offset).all())
    actions = [a for (a,) in db.query(AuditLog.action).distinct()
               .order_by(AuditLog.action)]
    return respond({
        "total": total,
        "actions": actions,
        "logs": [
            {
                "id": log.id,
                "username": username_ or "System",
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "details": log.details,
                "created_at": log.created_at.isoformat(),
            }
            for log, username_ in rows
        ],
    })


@bp.get("/users")
def users():
    db = get_db()
    sub_counts = dict(db.query(Submission.user_id, func.count(Submission.id))
                      .group_by(Submission.user_id).all())
    created_counts = dict(db.query(Campaign.created_by,
                                   func.count(Campaign.id))
                          .group_by(Campaign.created_by).all())
    rows = db.query(User).order_by(User.username).all()
    return respond([
        {
            "id": u.id, "username": u.username, "is_admin": u.is_admin,
            "registered_at": u.registered_at.isoformat(),
            "last_login_at": (u.last_login_at.isoformat()
                              if u.last_login_at else None),
            "submission_count": sub_counts.get(u.id, 0),
            "campaigns_created": created_counts.get(u.id, 0),
        }
        for u in rows
    ])


@bp.post("/users/<int:user_id>/set-admin")
def set_admin(user_id: int):
    db, acting = get_db(), require_admin()
    is_admin = request.args.get("is_admin", "").lower() in ("1", "true", "yes")
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(404, "User not found")
    if target.id == acting.id and not is_admin:
        raise HTTPException(400, "You cannot remove your own admin flag")
    target.is_admin = is_admin
    audit(db, acting, "set_admin", "user", target.id, {"is_admin": is_admin})
    db.commit()
    return respond({"id": target.id, "username": target.username,
                    "is_admin": target.is_admin})


_WIKI_DOMAIN_RE = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$")


@bp.put("/submissions/<int:submission_id>")
def edit_submission(submission_id: int):
    """Admin repair tool: fix a submitted page's title, the wiki it was
    filed against, or its moderation note (typo fixes, moved articles, a
    multi-language entry filed against the wrong project). Wiki metadata
    is refetched for the corrected page, so points follow the repair.

    Fields are optional; only the ones present in the body are changed.
    """
    db, acting = get_db(), require_admin()
    sub = db.get(Submission, submission_id)
    if sub is None:
        raise HTTPException(404, "Submission not found")
    data = request.get_json(silent=True) or {}

    old_title, old_domain = sub.title, sub.wiki_domain
    title = old_title
    if "title" in data:
        title = str(data.get("title") or "").strip()
        if not title:
            raise HTTPException(400, "A title is required")
    domain = old_domain
    if "wiki_domain" in data:
        domain = str(data.get("wiki_domain") or "").strip().lower()
        if not _WIKI_DOMAIN_RE.match(domain):
            raise HTTPException(
                400, "The wiki must be a domain like ml.wikipedia.org")

    if (title, domain) != (old_title, old_domain):
        duplicate = (db.query(Submission)
                     .filter_by(campaign_id=sub.campaign_id,
                                user_id=sub.user_id,
                                wiki_domain=domain, title=title)
                     .filter(Submission.id != sub.id).first())
        if duplicate:
            raise HTTPException(409, "This participant already submitted "
                                     "that title")
    sub.title = title
    sub.wiki_domain = domain
    if "moderation_note" in data:
        note = str(data.get("moderation_note") or "").strip()
        sub.moderation_note = note or None

    if ((title, domain) != (old_title, old_domain)
            and sub.kind in (SubmissionKind.article,
                             SubmissionKind.wikidata_item,
                             SubmissionKind.commons_file)):
        try:
            meta = mediawiki.fetch_page_metadata(
                domain, title, sub.user.username,
                sub.campaign.start_date, sub.campaign.end_date)
            if meta.exists:
                sub.page_id = meta.page_id
                sub.page_len = meta.page_len
                sub.current_rev_id = meta.current_rev_id
                sub.base_rev_id = meta.base_rev_id
                sub.bytes_added = meta.bytes_added
                sub.is_new_page = meta.is_new_page
                # The connected item decides the suggested-list bonus, so
                # it has to follow the page the submission now points at.
                sub.wikidata_qid = meta.wikidata_qid
        except Exception:
            pass
    audit(db, acting, "edit_submission", "submission", sub.id,
          {"campaign": sub.campaign.slug, "from": old_title, "to": title,
           "from_wiki": old_domain, "to_wiki": domain})
    db.commit()
    db.refresh(sub)
    return respond(submission_out(sub.campaign, sub))

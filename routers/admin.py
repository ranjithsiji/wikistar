"""Site administration: stats, audit log, user management."""
from flask import Blueprint, request
from sqlalchemy import desc, func

from auth import require_admin
from db import get_db
from models import AuditLog, Campaign, CampaignStatus, Submission, User
from routers.common import audit
from webutil import HTTPException, respond

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.before_request
def _gate():
    require_admin()


@bp.get("/stats")
def stats():
    db = get_db()
    return respond({
        "users": db.query(func.count(User.id)).scalar(),
        "campaigns": db.query(func.count(Campaign.id)).scalar(),
        "pending_campaigns": db.query(func.count(Campaign.id))
            .filter(Campaign.status == CampaignStatus.draft).scalar(),
        "submissions": db.query(func.count(Submission.id)).scalar(),
    })


@bp.get("/logs")
def logs():
    db = get_db()
    limit = min(max(request.args.get("limit", 50, type=int), 1), 200)
    offset = request.args.get("offset", 0, type=int)
    rows = (db.query(AuditLog, User.username)
            .outerjoin(User, AuditLog.user_id == User.id)
            .order_by(desc(AuditLog.created_at), desc(AuditLog.id))
            .limit(limit).offset(offset).all())
    return respond({
        "total": db.query(func.count(AuditLog.id)).scalar(),
        "logs": [
            {
                "id": log.id,
                "username": username or "System",
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "details": log.details,
                "created_at": log.created_at.isoformat(),
            }
            for log, username in rows
        ],
    })


@bp.get("/users")
def users():
    db = get_db()
    rows = db.query(User).order_by(User.username).all()
    return respond([
        {
            "id": u.id, "username": u.username, "is_admin": u.is_admin,
            "registered_at": u.registered_at.isoformat(),
            "last_login_at": (u.last_login_at.isoformat()
                              if u.last_login_at else None),
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

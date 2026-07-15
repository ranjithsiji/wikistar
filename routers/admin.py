"""Site administration: stats, audit log, user management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from auth import require_admin
from db import get_db
from models import AuditLog, Campaign, CampaignStatus, Submission, User
from routers.common import audit

router = APIRouter(prefix="/api/admin", tags=["admin"],
                   dependencies=[Depends(require_admin)])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return {
        "users": db.query(func.count(User.id)).scalar(),
        "campaigns": db.query(func.count(Campaign.id)).scalar(),
        "pending_campaigns": db.query(func.count(Campaign.id))
            .filter(Campaign.status == CampaignStatus.draft).scalar(),
        "submissions": db.query(func.count(Submission.id)).scalar(),
    }


@router.get("/logs")
def logs(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    limit = min(max(limit, 1), 200)
    rows = (db.query(AuditLog, User.username)
            .outerjoin(User, AuditLog.user_id == User.id)
            .order_by(desc(AuditLog.created_at), desc(AuditLog.id))
            .limit(limit).offset(offset).all())
    return {
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
    }


@router.get("/users")
def users(db: Session = Depends(get_db)):
    rows = db.query(User).order_by(User.username).all()
    return [
        {
            "id": u.id, "username": u.username, "is_admin": u.is_admin,
            "registered_at": u.registered_at.isoformat(),
            "last_login_at": (u.last_login_at.isoformat()
                              if u.last_login_at else None),
        }
        for u in rows
    ]


@router.post("/users/{user_id}/set-admin")
def set_admin(user_id: int, is_admin: bool,
              db: Session = Depends(get_db),
              acting: User = Depends(require_admin)):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(404, "User not found")
    if target.id == acting.id and not is_admin:
        raise HTTPException(400, "You cannot remove your own admin flag")
    target.is_admin = is_admin
    audit(db, acting, "set_admin", "user", target.id, {"is_admin": is_admin})
    db.commit()
    return {"id": target.id, "username": target.username,
            "is_admin": target.is_admin}

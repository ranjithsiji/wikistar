"""Site administration: stats, audit log, user management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import require_admin
from db import get_db
from models import User

router = APIRouter(prefix="/api/admin", tags=["admin"],
                   dependencies=[Depends(require_admin)])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    raise HTTPException(501, "Phase 2")


@router.get("/logs")
def logs(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    raise HTTPException(501, "Phase 2")


@router.get("/users")
def users(db: Session = Depends(get_db)):
    raise HTTPException(501, "Phase 2")


@router.post("/users/{user_id}/set-admin")
def set_admin(user_id: int, is_admin: bool, db: Session = Depends(get_db)):
    raise HTTPException(501, "Phase 2")

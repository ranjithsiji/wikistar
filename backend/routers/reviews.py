"""Jury reviews — the single write path for judging (replaces the three
overlapping v1 endpoints /judge, /marks and /jury-review).

PUT is an upsert on (submission_id, reviewer_id): a juror has exactly one
review per submission and can revise it until the campaign is archived.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import require_user
from backend.db import get_db
from backend.models import User
from backend.schemas import ReviewIn, ReviewOut

router = APIRouter(prefix="/api", tags=["reviews"])


@router.put("/submissions/{submission_id}/review", response_model=ReviewOut)
def upsert_review(submission_id: int, payload: ReviewIn,
                  db: Session = Depends(get_db),
                  user: User = Depends(require_user)):
    """Jury/organizer of the submission's campaign only."""
    raise HTTPException(501, "Phase 2")


@router.delete("/submissions/{submission_id}/review", status_code=204)
def delete_own_review(submission_id: int, db: Session = Depends(get_db),
                      user: User = Depends(require_user)):
    raise HTTPException(501, "Phase 2")

"""Submissions: participants add their contributions to a campaign.

Permissions
-----------
list                 public for active+ campaigns
create               logged-in user; auto-joins campaign as participant;
                     blocked for jury members unless campaign.jury_can_submit
delete               owner (while campaign active), organizer, admin
refresh-metadata     owner, organizer or admin — re-fetches wiki metadata
accept/reject        organizer or admin (status + optional points_override)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import require_user
from backend.db import get_db
from backend.models import User
from backend.schemas import SubmissionIn, SubmissionOut

router = APIRouter(prefix="/api", tags=["submissions"])


@router.get("/campaigns/{slug}/submissions", response_model=list[SubmissionOut])
def list_submissions(slug: str, db: Session = Depends(get_db)):
    """Each submission includes its live point breakdown."""
    raise HTTPException(501, "Phase 2")


@router.post("/campaigns/{slug}/submissions", response_model=SubmissionOut,
             status_code=201)
def create_submission(slug: str, payload: SubmissionIn,
                      db: Session = Depends(get_db),
                      user: User = Depends(require_user)):
    """Identity from session. Fetches MediaWiki metadata (bytes added,
    new-page check) at submission time; failures are non-fatal."""
    raise HTTPException(501, "Phase 2")


@router.delete("/submissions/{submission_id}", status_code=204)
def delete_submission(submission_id: int, db: Session = Depends(get_db),
                      user: User = Depends(require_user)):
    raise HTTPException(501, "Phase 2")


@router.post("/submissions/{submission_id}/refresh", response_model=SubmissionOut)
def refresh_metadata(submission_id: int, db: Session = Depends(get_db),
                     user: User = Depends(require_user)):
    raise HTTPException(501, "Phase 2")


@router.post("/submissions/{submission_id}/moderate", response_model=SubmissionOut)
def moderate_submission(submission_id: int, db: Session = Depends(get_db),
                        user: User = Depends(require_user)):
    """Organizer final say: accept/reject and optional points_override."""
    raise HTTPException(501, "Phase 2")

"""Self-assessment claims.

Participants claim points on their own submissions under the campaign's
scoring rules; points are always recomputed server-side from the rule and
quantity (backend.scoring.claim_points). Organizers verify, adjust or
reject each claim — their decision (points_final) wins.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import require_user
from backend.db import get_db
from backend.models import User
from backend.schemas import ClaimIn, ClaimModeration, ClaimOut, SubmissionOut

router = APIRouter(prefix="/api", tags=["claims"])


@router.put("/submissions/{submission_id}/claims", response_model=SubmissionOut)
def upsert_claims(submission_id: int, payload: list[ClaimIn],
                  db: Session = Depends(get_db),
                  user: User = Depends(require_user)):
    """Owner only. Replaces the participant's claim set for this
    submission (one claim per rule); returns the recomputed breakdown."""
    raise HTTPException(501, "Phase 2")


@router.post("/claims/{claim_id}/moderate", response_model=ClaimOut)
def moderate_claim(claim_id: int, payload: ClaimModeration,
                   db: Session = Depends(get_db),
                   user: User = Depends(require_user)):
    """Organizer/jury of the campaign: verify / adjust / reject."""
    raise HTTPException(501, "Phase 2")

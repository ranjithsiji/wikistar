"""Campaign CRUD, lifecycle and membership.

Permissions
-----------
list/detail          public (draft/rejected visible to organizer+admin only)
create               any logged-in user; creator becomes organizer
update               organizer or admin
delete               admin, or organizer while still draft
approve/reject       admin
members add/remove   organizer or admin
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import require_user
from db import get_db
from models import Campaign, User
from schemas import CampaignDetail, CampaignIn, CampaignSummary, LeaderboardRow

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


def get_campaign_or_404(db: Session, slug: str) -> Campaign:
    campaign = db.query(Campaign).filter_by(slug=slug).first()
    if campaign is None:
        raise HTTPException(404, "Campaign not found")
    return campaign


@router.get("", response_model=list[CampaignSummary])
def list_campaigns(db: Session = Depends(get_db)):
    raise HTTPException(501, "Phase 2")


@router.post("", response_model=CampaignDetail, status_code=201)
def create_campaign(payload: CampaignIn, db: Session = Depends(get_db),
                    user: User = Depends(require_user)):
    """Creates the campaign in draft status; slug auto-generated from the
    name when omitted; scoring rules, jury and suggested pages inline."""
    raise HTTPException(501, "Phase 2")


@router.get("/{slug}", response_model=CampaignDetail)
def campaign_detail(slug: str, db: Session = Depends(get_db)):
    raise HTTPException(501, "Phase 2")


@router.put("/{slug}", response_model=CampaignDetail)
def update_campaign(slug: str, payload: CampaignIn, db: Session = Depends(get_db),
                    user: User = Depends(require_user)):
    """Replaces campaign fields, rules, jury list and suggested pages."""
    raise HTTPException(501, "Phase 2")


@router.delete("/{slug}", status_code=204)
def delete_campaign(slug: str, db: Session = Depends(get_db),
                    user: User = Depends(require_user)):
    raise HTTPException(501, "Phase 2")


@router.post("/{slug}/approve", response_model=CampaignDetail)
def approve_campaign(slug: str, db: Session = Depends(get_db),
                     user: User = Depends(require_user)):
    raise HTTPException(501, "Phase 2")


@router.post("/{slug}/reject", response_model=CampaignDetail)
def reject_campaign(slug: str, db: Session = Depends(get_db),
                    user: User = Depends(require_user)):
    raise HTTPException(501, "Phase 2")


@router.get("/{slug}/leaderboard", response_model=list[LeaderboardRow])
def leaderboard(slug: str, db: Session = Depends(get_db)):
    """Ranking computed live via scoring.compute_breakdown."""
    raise HTTPException(501, "Phase 2")

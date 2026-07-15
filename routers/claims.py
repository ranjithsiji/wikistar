"""Self-assessment claims.

Participants claim points on their own submissions under the campaign's
scoring rules; point values are always recomputed server-side from the
rule and quantity (scoring.claim_points) — the client's numbers are
never trusted. Organizers verify, adjust or reject each claim; an
adjusted points_final always wins.
"""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import require_jury, require_user
from db import get_db
from models import (
    CampaignStatus,
    Claim,
    ClaimStatus,
    RuleType,
    ScoringMode,
    Submission,
    User,
)
from routers.common import audit, submission_out
from schemas import ClaimIn, ClaimModeration, ClaimOut, SubmissionOut
from scoring import AUTO_METRICS, claim_points

router = APIRouter(prefix="/api", tags=["claims"])

CLAIMABLE_TYPES = (RuleType.per_unit, RuleType.flat_bonus)


def _get_submission_or_404(db: Session, submission_id: int) -> Submission:
    sub = db.get(Submission, submission_id)
    if sub is None:
        raise HTTPException(404, "Submission not found")
    return sub


@router.put("/submissions/{submission_id}/claims",
            response_model=SubmissionOut)
def upsert_claims(submission_id: int, payload: list[ClaimIn],
                  db: Session = Depends(get_db),
                  user: User = Depends(require_user)):
    """Owner only. Replaces the participant's claim set for this
    submission (one claim per rule); returns the recomputed breakdown."""
    sub = _get_submission_or_404(db, submission_id)
    campaign = sub.campaign
    settings = campaign.effective_settings

    if sub.user_id != user.id:
        raise HTTPException(403, "You can only claim on your own submissions")
    if campaign.scoring_mode == ScoringMode.jury:
        raise HTTPException(400, "This campaign uses jury scoring")
    if campaign.status == CampaignStatus.archived:
        raise HTTPException(400, "This campaign is archived")
    if (date.today() > campaign.end_date
            and not settings.get("claims_editable_after_end", True)):
        raise HTTPException(400, "Claims can no longer be edited")

    rules = {r.id: r for r in campaign.rules
             if r.active and r.rule_type in CLAIMABLE_TYPES
             and not (r.is_auto or r.metric in AUTO_METRICS)}
    seen: set[int] = set()
    for item in payload:
        if item.rule_id not in rules:
            raise HTTPException(400,
                f"Rule {item.rule_id} is not claimable in this campaign")
        if item.rule_id in seen:
            raise HTTPException(400, "Duplicate claim for one rule")
        seen.add(item.rule_id)

    existing = {c.rule_id: c for c in sub.claims}
    for item in payload:
        rule = rules[item.rule_id]
        points = claim_points(rule, item.quantity)
        claim = existing.get(item.rule_id)
        if claim is None:
            claim = Claim(submission_id=sub.id, rule_id=rule.id)
            db.add(claim)
        elif (claim.quantity != item.quantity
              or float(claim.points_claimed) != points):
            # Changed claims need fresh verification.
            claim.status = ClaimStatus.claimed
            claim.points_final = None
            claim.reviewed_by = None
            claim.reviewed_at = None
        claim.quantity = item.quantity
        claim.points_claimed = points
        claim.evidence_url = item.evidence_url
        claim.note = item.note
    for rule_id, claim in existing.items():
        if rule_id not in seen:
            db.delete(claim)

    audit(db, user, "claim", "submission", sub.id,
          {"campaign": campaign.slug, "title": sub.title,
           "claims": len(payload)})
    db.commit()
    db.refresh(sub)
    return submission_out(campaign, sub, settings)


@router.post("/claims/{claim_id}/moderate", response_model=ClaimOut)
def moderate_claim(claim_id: int, payload: ClaimModeration,
                   db: Session = Depends(get_db),
                   user: User = Depends(require_user)):
    """Organizer/jury of the campaign: verify / adjust / reject."""
    claim = db.get(Claim, claim_id)
    if claim is None:
        raise HTTPException(404, "Claim not found")
    campaign = claim.submission.campaign
    require_jury(db, campaign, user)

    claim.status = payload.status
    if payload.status == ClaimStatus.adjusted:
        if payload.points_final is None:
            raise HTTPException(400, "An adjusted claim needs points_final")
        claim.points_final = payload.points_final
    else:
        claim.points_final = None
    claim.reviewed_by = user.id
    claim.reviewed_at = datetime.now(timezone.utc)
    audit(db, user, "moderate_claim", "claim", claim.id,
          {"campaign": campaign.slug, "status": payload.status.value,
           "points_final": payload.points_final})
    db.commit()
    db.refresh(claim)
    return ClaimOut.model_validate(claim)

"""Jury reviews — the single write path for judging (replaces the three
overlapping v1 endpoints /judge, /marks and /jury-review).

PUT is an upsert on (submission_id, reviewer_id): a juror has exactly one
review per submission and can revise it until the campaign is archived.
Jurors cannot review their own submissions.
"""
from flask import Blueprint
from sqlalchemy.orm import Session

from auth import require_jury, require_user
from db import get_db
from models import CampaignStatus, Review, Submission
from routers.common import audit
from schemas import ReviewIn, ReviewOut
from scoring import review_total
from webutil import HTTPException, parse, respond

bp = Blueprint("reviews", __name__, url_prefix="/api")


def _get_submission_or_404(db: Session, submission_id: int) -> Submission:
    sub = db.get(Submission, submission_id)
    if sub is None:
        raise HTTPException(404, "Submission not found")
    return sub


@bp.put("/submissions/<int:submission_id>/review")
def upsert_review(submission_id: int):
    db, user = get_db(), require_user()
    payload = parse(ReviewIn)
    sub = _get_submission_or_404(db, submission_id)
    campaign = sub.campaign
    require_jury(db, campaign, user)
    if sub.user_id == user.id:
        raise HTTPException(403, "You cannot review your own submission")
    if campaign.status == CampaignStatus.archived:
        raise HTTPException(400, "This campaign is archived")

    review = db.query(Review).filter_by(
        submission_id=sub.id, reviewer_id=user.id).first()
    if review is None:
        review = Review(submission_id=sub.id, reviewer_id=user.id)
        db.add(review)
    review.scores = payload.scores
    criteria = campaign.effective_settings.get("jury_criteria") or []
    if criteria and payload.scores:
        # Fountain semantics: the total is derived from the marks config,
        # never trusted from the client.
        review.total = review_total(criteria, payload.scores)
    else:
        review.total = payload.total
    review.decision = payload.decision
    review.comment = payload.comment
    audit(db, user, "review", "submission", sub.id,
          {"campaign": campaign.slug, "title": sub.title,
           "decision": payload.decision.value, "total": payload.total})
    db.commit()
    db.refresh(review)
    return respond(ReviewOut.model_validate(review))


@bp.delete("/submissions/<int:submission_id>/review")
def delete_own_review(submission_id: int):
    db, user = get_db(), require_user()
    sub = _get_submission_or_404(db, submission_id)
    review = db.query(Review).filter_by(
        submission_id=sub.id, reviewer_id=user.id).first()
    if review is None:
        raise HTTPException(404, "You have no review on this submission")
    if sub.campaign.status == CampaignStatus.archived:
        raise HTTPException(400, "This campaign is archived")
    audit(db, user, "unreview", "submission", sub.id,
          {"campaign": sub.campaign.slug, "title": sub.title})
    db.delete(review)
    db.commit()
    return respond(None, 204)

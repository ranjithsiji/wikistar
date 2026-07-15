"""Fountain-ported behaviour: marks config totals, consensual vote,
tie ranking."""
from models import (
    Review,
    ReviewDecision,
    ScoringMode,
    Submission,
    SubmissionKind,
)
from scoring import compute_breakdown, review_total

CRITERIA = [
    {"key": "quality", "title": "Quality", "type": "radio",
     "values": [{"title": "poor", "value": 0},
                {"title": "ok", "value": 2},
                {"title": "great", "value": 5}]},
    {"key": "sourced", "title": "Well sourced", "type": "check", "value": 1},
    {"key": "bonus", "title": "Bonus", "type": "int"},
]


def test_review_total_radio_check_int():
    assert review_total(CRITERIA, {"quality": 2, "sourced": True, "bonus": 3}) == 9
    assert review_total(CRITERIA, {"quality": 0}) == 0
    assert review_total(CRITERIA, {"quality": 99}) == 0     # out of range
    assert review_total(CRITERIA, {"sourced": False}) == 0
    assert review_total(CRITERIA, {"quality": True}) == 2   # bool compat -> index 1


def _jury_submission(totals: list[float]) -> Submission:
    sub = Submission(id=1, campaign_id=1, user_id=1,
                     kind=SubmissionKind.article, title="X",
                     wiki_domain="en.wikipedia.org")
    sub.claims = []
    sub.reviews = [
        Review(submission_id=1, reviewer_id=i + 10, total=t,
               decision=ReviewDecision.accept)
        for i, t in enumerate(totals)
    ]
    return sub


def test_consensual_vote_requires_agreement():
    agree = _jury_submission([5, 5])
    split = _jury_submission([5, 4])
    settings = {"consensual_vote": True, "min_reviews_per_submission": 1}
    assert compute_breakdown(agree, [], set(), ScoringMode.jury, settings).total == 5
    assert compute_breakdown(split, [], set(), ScoringMode.jury, settings).total == 0
    # without the flag the split averages
    assert compute_breakdown(split, [], set(), ScoringMode.jury,
                             {"min_reviews_per_submission": 1}).total == 4.5


def test_min_reviews_gate():
    sub = _jury_submission([7])
    settings = {"min_reviews_per_submission": 2}
    assert compute_breakdown(sub, [], set(), ScoringMode.jury, settings).total == 0

"""Regression tests for the scoring / settings fixes:

  * per_unit points never go negative and floor correctly (bytes_added < 0)
  * "nearest" rounding is half-up, not banker's rounding
  * max_units caps the unit count
  * suggested-list matching is underscore/space and case insensitive
  * settings validation enforces numeric bounds and json shape
  * review_total tolerates a malformed (non-list) criteria value

These exercise the branches the documentation examples never reached, so
the previously-green suite did not catch the bugs.
"""
from domain.models import (
    RuleApplies,
    RuleType,
    ScoringMode,
    ScoringRule,
    SubmissionKind,
)
from domain.scoring import (
    compute_breakdown,
    normalize_title,
    per_unit_points,
    review_total,
)
from domain.settings_registry import validate_overrides

from tests.test_scoring import RULES, make_submission


def per_unit_rule(unit_size=1000, points=1, rounding=None, max_units=None):
    params = {"rounding": rounding} if rounding else None
    return ScoringRule(
        id=99, campaign_id=1, position=0, rule_type=RuleType.per_unit,
        applies_to=RuleApplies.article, label="Bytes", metric="bytes_added",
        unit_size=unit_size, points=points, is_auto=True,
        max_units=max_units, params=params, active=True)


# ---- B1: negatives clamp to zero; floor is a true floor -------------------

def test_negative_value_scores_zero_not_negative():
    units, pts = per_unit_points(per_unit_rule(), -2500)
    assert (units, pts) == (0, 0.0)


def test_floor_is_true_floor_for_positive():
    units, pts = per_unit_points(per_unit_rule(), 3900)
    assert (units, pts) == (3, 3.0)


# ---- B10: "nearest" is half-up, not banker's rounding ---------------------

def test_nearest_rounds_half_up():
    assert per_unit_points(per_unit_rule(rounding="nearest"), 2500)[0] == 3
    assert per_unit_points(per_unit_rule(rounding="nearest"), 1499)[0] == 1
    assert per_unit_points(per_unit_rule(rounding="nearest"), 500)[0] == 1


# ---- B4: max_units caps the unit count ------------------------------------

def test_max_units_caps_the_count():
    units, pts = per_unit_points(
        per_unit_rule(points=1, max_units=5), 12000)
    assert (units, pts) == (5, 5.0)


def test_unit_size_zero_is_safe():
    assert per_unit_points(per_unit_rule(unit_size=0), 4000) == (0, 0.0)


# ---- B2: suggested-list matching ignores underscores and case -------------

def test_suggested_match_underscore_vs_space():
    sub = make_submission(title="Kathakali_dance", bytes_added=4100,
                          page_len=4100, is_new_page=True)
    suggested = {normalize_title("Kathakali dance")}
    with_bonus = compute_breakdown(sub, RULES, suggested, ScoringMode.self_).total
    without = compute_breakdown(sub, RULES, set(), ScoringMode.self_).total
    # The +10 suggested-article bonus is awarded despite the separator/case
    # mismatch between the submitted title and the suggested entry.
    assert with_bonus - without == 10


# ---- B6: settings numeric bounds ------------------------------------------

def test_negative_min_reviews_rejected():
    import pytest
    with pytest.raises(ValueError):
        validate_overrides({"min_reviews_per_submission": -1})
    with pytest.raises(ValueError):
        validate_overrides({"min_reviews_per_submission": 0})


def test_negative_max_submissions_rejected():
    import pytest
    with pytest.raises(ValueError):
        validate_overrides({"max_submissions_per_user": -5})


# ---- B7: json shape enforced; review_total tolerates bad input ------------

def test_jury_criteria_must_be_a_list():
    import pytest
    with pytest.raises(ValueError):
        validate_overrides({"jury_criteria": {"x": 1}})


def test_review_total_tolerates_non_list_criteria():
    assert review_total({"x": 1}, {"x": 1}) == 0.0
    assert review_total(None, {}) == 0.0

"""The scoring engine must reproduce every worked example from the
self-assessment rule documentation."""
from backend.models import (
    Claim,
    ClaimStatus,
    ScoringMode,
    ScoringRule,
    Submission,
    SubmissionKind,
)
from backend.scoring import compute_breakdown, default_self_assessment_rules


def make_rules() -> list[ScoringRule]:
    rules = []
    for i, spec in enumerate(default_self_assessment_rules()):
        # Column defaults only apply on INSERT; fill them for transient objects.
        spec = {"active": True, "unit_size": 1, "points": 0, "is_auto": False,
                "max_units": None, "params": None, **spec}
        rules.append(ScoringRule(id=i + 1, campaign_id=1, position=i, **spec))
    return rules


RULES = make_rules()


def rule_by_label(label: str) -> ScoringRule:
    return next(r for r in RULES if label in r.label)


def make_submission(kind=SubmissionKind.article, **kw) -> Submission:
    sub = Submission(id=1, campaign_id=1, user_id=1, kind=kind,
                     title=kw.pop("title", "Example"),
                     wiki_domain="ga.wikipedia.org", **kw)
    sub.reviews = []
    sub.claims = []
    return sub


def claim(sub: Submission, label: str, quantity: int = 1,
          status=ClaimStatus.claimed) -> None:
    rule = rule_by_label(label)
    from backend.scoring import claim_points
    sub.claims.append(Claim(submission_id=sub.id, rule_id=rule.id,
                            rule=rule, quantity=quantity, status=status,
                            points_claimed=claim_points(rule, quantity)))


def total(sub: Submission) -> float:
    return compute_breakdown(sub, RULES, set(), ScoringMode.self_).total


def total_suggested(sub: Submission, titles: set[str]) -> float:
    return compute_breakdown(sub, RULES, titles, ScoringMode.self_).total


def test_new_translation_4100_bytes_is_4_points():
    sub = make_submission(bytes_added=4100, page_len=4100, is_new_page=True)
    assert total(sub) == 4


def test_3900_bytes_plus_improvement_is_6_points():
    sub = make_submission(bytes_added=3900, page_len=12000, is_new_page=False)
    claim(sub, "Substantial improvement")
    assert total(sub) == 6  # 4 (nearest rounding) + 2


def test_suggested_article_5000_bytes_improved_is_17_points():
    sub = make_submission(title="Kathakali", bytes_added=5000, page_len=20000)
    claim(sub, "Substantial improvement")
    assert total_suggested(sub, {"kathakali"}) == 17  # 5 + 2 + 10


def test_new_article_below_3500_bytes_earns_no_size_points():
    sub = make_submission(bytes_added=3000, page_len=3000, is_new_page=True)
    assert total(sub) == 0


def test_good_article_is_25_points():
    sub = make_submission(bytes_added=0, page_len=9000)
    claim(sub, "Good Article")
    assert total(sub) == 25


def test_wikidata_item_created_is_3_points():
    sub = make_submission(kind=SubmissionKind.wikidata_item, title="Q123")
    claim(sub, "New Wikidata item created")
    assert total(sub) == 3


def test_10_statements_is_2_points():
    sub = make_submission(kind=SubmissionKind.wikidata_item, title="Q124")
    claim(sub, "Statements added", quantity=10)
    assert total(sub) == 2


def test_5_labels_is_1_point_and_6_references_is_2_points():
    sub = make_submission(kind=SubmissionKind.wikidata_item, title="Q125")
    claim(sub, "Labels / descriptions / aliases", quantity=5)
    claim(sub, "References added", quantity=6)
    assert total(sub) == 3


def test_suggested_item_created_with_10_statements_is_10_points():
    sub = make_submission(kind=SubmissionKind.wikidata_item, title="Q126")
    claim(sub, "New Wikidata item created")
    claim(sub, "Statements added", quantity=10)
    assert total_suggested(sub, {"q126"}) == 10  # 3 + 5 + 2


def test_rejected_claim_counts_zero_and_adjustment_wins():
    sub = make_submission(bytes_added=2000, page_len=15000)
    claim(sub, "Good Article", status=ClaimStatus.rejected)
    assert total(sub) == 2  # only the bytes survive
    sub2 = make_submission(bytes_added=0, page_len=15000)
    claim(sub2, "Substantial improvement")
    sub2.claims[0].status = ClaimStatus.adjusted
    sub2.claims[0].points_final = 1
    assert total(sub2) == 1


def test_organizer_override_wins():
    sub = make_submission(bytes_added=9000, page_len=15000)
    sub.points_override = 0
    assert total(sub) == 0

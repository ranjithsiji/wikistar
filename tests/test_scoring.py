"""The scoring engine must reproduce every worked example from the
self-assessment rule documentation."""
from domain.models import (
    Claim,
    ClaimStatus,
    ScoringMode,
    ScoringRule,
    Submission,
    SubmissionKind,
)
from domain.scoring import compute_breakdown, default_self_assessment_rules


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
    from domain.scoring import claim_points
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


def test_3900_bytes_plus_improvement_is_5_points():
    sub = make_submission(bytes_added=3900, page_len=12000, is_new_page=False)
    claim(sub, "Substantial improvement")
    assert total(sub) == 5  # 3 (bytes, floor) + 2


def test_bytes_rule_floors_not_rounds():
    # 6,550 bytes -> 6 points, not 7: the byte rule takes the lower whole
    # unit (floor), it does not round to the nearest thousand.
    sub = make_submission(bytes_added=6550, page_len=6550, is_new_page=True)
    assert total(sub) == 6


def test_suggested_article_5000_bytes_improved_is_17_points():
    # The article is matched to the list by its connected Wikidata item.
    sub = make_submission(title="Kathakali", bytes_added=5000, page_len=20000,
                          wikidata_qid="Q126")
    claim(sub, "Substantial improvement")
    assert total_suggested(sub, {"Q126"}) == 17  # 5 + 2 + 10


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


def test_5_labels_is_1_point_and_references_are_per_unit():
    sub = make_submission(kind=SubmissionKind.wikidata_item, title="Q125")
    claim(sub, "Labels / descriptions / aliases", quantity=5)
    claim(sub, "References added", quantity=6)  # 1 point each since v2.1
    assert total(sub) == 7


def test_suggested_item_created_with_10_statements_is_10_points():
    # is_new_page=True stands in for the fetched-metadata evidence that
    # the submitter actually created this item (the suggested-list bonus
    # requires a verifiable contribution, not just a claim).
    sub = make_submission(kind=SubmissionKind.wikidata_item, title="Q126",
                          is_new_page=True)
    claim(sub, "New Wikidata item created")
    claim(sub, "Statements added", quantity=10)
    assert total_suggested(sub, {"q126"}) == 10  # 3 + 5 + 2


def test_item_statement_and_term_edits_score_without_claims():
    # Q6427374-style case: the submitter made 7 statement edits and 2
    # term edits on one item, all counted from the wiki history into
    # Submission.metrics. Those per_unit rules must score from the fetched
    # metrics, exactly as they do for a bulk wikidata_edits submission —
    # the participant should not have to also claim what the engine
    # already measured.
    sub = make_submission(kind=SubmissionKind.wikidata_item, title="Q6427374")
    sub.metrics = {"statements": 7, "terms": 2}
    # 7 statements -> floor(7/5) = 1 point; 2 terms -> floor(2/5) = 0.
    assert total(sub) == 1
    # ...and with the suggested-list bonus (9 edits clears the gate).
    assert total_suggested(sub, {"q6427374"}) == 6


def test_item_metrics_are_not_double_counted_with_claims():
    # A claim on a rule the engine already scored from metrics must not
    # add a second line for the same work.
    sub = make_submission(kind=SubmissionKind.wikidata_item, title="Q555")
    sub.metrics = {"statements": 10, "terms": 0}
    claim(sub, "Statements added", quantity=10)
    assert total(sub) == 2


def test_suggested_item_bonus_needs_5_real_edits():
    # metrics (statements + terms) come from the live Wikidata fetch, not
    # claims -- this is the actual gate compute_breakdown enforces for a
    # single wikidata_item submission's suggested-list bonus.
    sub = make_submission(kind=SubmissionKind.wikidata_item, title="Q127")
    sub.metrics = {"statements": 2, "terms": 1}  # 3 total, below the gate
    assert total_suggested(sub, {"q127"}) == 0

    sub2 = make_submission(kind=SubmissionKind.wikidata_item, title="Q128")
    sub2.metrics = {"statements": 3, "terms": 2}  # 5 total, meets the gate
    assert total_suggested(sub2, {"q128"}) == 5

    # a brand-new item counts even with fewer than 5 term/statement edits
    sub3 = make_submission(kind=SubmissionKind.wikidata_item, title="Q129",
                           is_new_page=True)
    sub3.metrics = {"statements": 1, "terms": 0}
    assert total_suggested(sub3, {"q129"}) == 5


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


# ---- rule-based points in jury / hybrid modes ------------------------------

def _accept_review(sub: Submission, total: float, reviewer_id: int = 10) -> None:
    from domain.models import Review, ReviewDecision
    sub.reviews.append(Review(submission_id=sub.id, reviewer_id=reviewer_id,
                              total=total, decision=ReviewDecision.accept))


def test_jury_mode_counts_campaign_rules_plus_jury_average():
    sub = make_submission(bytes_added=5000, page_len=20000, wikidata_qid="Q126")
    _accept_review(sub, 7)
    bd = compute_breakdown(sub, RULES, {"Q126"}, ScoringMode.jury)
    # 5 (bytes, floor) + 10 (suggested list) + 7 (jury average)
    assert bd.total == 22
    assert {l.source for l in bd.lines} == {"auto", "jury"}


def test_jury_mode_ignores_claims():
    sub = make_submission(bytes_added=0, page_len=9000)
    claim(sub, "Good Article")
    assert compute_breakdown(sub, RULES, set(), ScoringMode.jury).total == 0


def test_hybrid_mode_combines_claims_and_jury_average():
    sub = make_submission(bytes_added=2000, page_len=15000)
    claim(sub, "Substantial improvement")
    _accept_review(sub, 3)
    bd = compute_breakdown(sub, RULES, set(), ScoringMode.hybrid)
    assert bd.total == 7  # 2 (bytes) + 2 (claim) + 3 (jury)


def test_article_matches_suggested_item_by_sitelink():
    # An article connected to a suggested Wikidata item earns the
    # suggested-list bonus even though its title was not listed.
    sub = make_submission(title="Some Local Title", bytes_added=5000,
                          page_len=20000, wikidata_qid="Q126")
    # keys as built by common.suggested_titles for articles: item QIDs
    # are added uppercased alongside any suggested article titles.
    assert total_suggested(sub, {"Q126"}) == 15  # 5 bytes + 10 suggested
    # a different connected item does not match
    sub2 = make_submission(title="Some Local Title", bytes_added=5000,
                           page_len=20000, wikidata_qid="Q999")
    assert total_suggested(sub2, {"Q126"}) == 5   # bytes only
    # An article with no connected item cannot be matched at all, even
    # when its title is exactly the one on the list: the QID is what
    # identifies the subject across spellings and language editions.
    sub3 = make_submission(title="Kathakali", bytes_added=5000, page_len=20000)
    assert total_suggested(sub3, {"kathakali", "Q126"}) == 5
    # ...and the breakdown says why, instead of silently scoring nothing.
    bd = compute_breakdown(sub3, RULES, {"kathakali", "Q126"}, ScoringMode.self_)
    assert any("not connected to a Wikidata item" in line.label
               for line in bd.lines)

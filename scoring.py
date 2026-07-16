"""Configurable scoring engine.

A campaign's score sheet is a list of ScoringRule rows. For every
submission the engine produces a breakdown of point lines from three
sources:

  auto    — computed from wiki metadata stored on the submission
            (bytes_added, is_new_page, suggested list membership);
            applies in every scoring mode
  claimed — entered by the participant as Claim rows (self / hybrid)
  jury    — Review rows (jury / hybrid); averaged per submission and
            added on top of the rule-based points

`submission.points_override`, when set by an organizer, replaces the
computed total — the organizers always have the final say.

Rule semantics
--------------
per_unit        floor(value / unit_size) * points, value capped at
                max_units * unit_size when max_units is set.
                metric "bytes_added" is auto; other metrics (statements,
                labels_descriptions_aliases, references, ...) come from
                the participant's claim quantity.
per_unit gate:  if the submission is a new page and a threshold rule
                defines min_new_article_bytes, a too-short new article
                earns 0 from "bytes_added".
flat_bonus      points once per submission; auto triggers may be added
                later (e.g. good_article via the MW API), today they are
                claimed and verified by organizers.
suggested_list  points when submission.title is on suggested_pages
                (matched case-insensitively, per kind). Auto.
threshold       gate only, no points (params: {"min_new_article_bytes": N}).
eligibility     documentation of topical constraints shown to
                participants and organizers, no points.
"""
from dataclasses import dataclass, field

from models import (
    Claim,
    ClaimStatus,
    ReviewDecision,
    RuleApplies,
    RuleType,
    ScoringMode,
    ScoringRule,
    Submission,
    SubmissionKind,
)

# Metrics the engine can compute on its own from submission metadata.
AUTO_METRICS = {"bytes_added"}

# Bulk kinds cover a user's whole activity in the campaign window; their
# per_unit rules score from Submission.metrics counts (rule metric ->
# metrics key) instead of claims.
BULK_KIND_METRICS: dict[SubmissionKind, dict[str, str]] = {
    SubmissionKind.wikidata_edits: {
        "statements": "statements",
        "labels_descriptions_aliases": "terms",
    },
    SubmissionKind.commons_edits: {
        "image_added": "uploads",
        "depicts_added": "depicts",
    },
}

# Bulk kinds reuse the rules of their per-page counterpart.
RULE_KIND = {
    SubmissionKind.wikidata_edits: SubmissionKind.wikidata_item,
    SubmissionKind.commons_edits: SubmissionKind.commons_file,
}


@dataclass
class PointLine:
    rule_id: int | None
    label: str
    source: str          # "auto" | "claimed" | "jury" | "override"
    quantity: float
    points: float
    status: str = ""     # claim status, when source == "claimed"


@dataclass
class Breakdown:
    lines: list[PointLine] = field(default_factory=list)
    total: float = 0.0

    def add(self, line: PointLine) -> None:
        self.lines.append(line)
        self.total = round(self.total + line.points, 2)


def rule_applies(rule: ScoringRule, submission: Submission) -> bool:
    kind = RULE_KIND.get(submission.kind, submission.kind)
    return rule.active and rule.applies_to in (
        RuleApplies.any,
        RuleApplies(kind.value),
    )


def per_unit_points(rule: ScoringRule, value: float) -> tuple[int, float]:
    """Return (units, points) for a per_unit rule.

    params.rounding: "floor" (default) or "nearest". The documented byte
    rule rounds to nearest (3,900 bytes -> 4 points), count-based metrics
    like statements use floor.
    """
    if rule.unit_size <= 0:
        return 0, 0.0
    rounding = (rule.params or {}).get("rounding", "floor")
    ratio = value / rule.unit_size
    units = round(ratio) if rounding == "nearest" else int(ratio)
    if rule.max_units is not None:
        units = min(units, rule.max_units)
    return units, round(units * float(rule.points), 2)


def claim_points(rule: ScoringRule, quantity: int) -> float:
    """Server-side value of a participant claim (never trusted from client)."""
    if rule.rule_type == RuleType.per_unit:
        _, pts = per_unit_points(rule, quantity)
        return pts
    if rule.rule_type in (RuleType.flat_bonus, RuleType.suggested_list):
        return float(rule.points)
    return 0.0


def _min_new_article_bytes(rules: list[ScoringRule]) -> int | None:
    for rule in rules:
        if rule.rule_type == RuleType.threshold and rule.params:
            value = rule.params.get("min_new_article_bytes")
            if value:
                return int(value)
    return None


def compute_breakdown(
    submission: Submission,
    rules: list[ScoringRule],
    suggested_titles: set[str],
    scoring_mode: ScoringMode,
    settings: dict | None = None,
) -> Breakdown:
    """Full point breakdown for one submission.

    suggested_titles: lowercase titles of the campaign's suggested pages
    matching this submission's kind.
    settings: the campaign's effective settings; honours
    min_reviews_per_submission (jury) and unverified_claims_count (self).
    """
    settings = settings or {}
    bd = Breakdown()

    if submission.points_override is not None:
        bd.add(PointLine(None, "Organizer override", "override", 1,
                         float(submission.points_override)))
        return bd

    # ---- rule-based points: every scoring mode ----------------------------
    # The campaign's score sheet always applies; the modes only differ in
    # who enters the human-judged part (claims vs jury marks).
    applicable = [r for r in rules if rule_applies(r, submission)]
    min_new_bytes = _min_new_article_bytes(applicable)
    claims_by_rule: dict[int, Claim] = {c.rule_id: c for c in submission.claims}

    bulk = BULK_KIND_METRICS.get(submission.kind)
    for rule in applicable:
        # Bulk kinds: per_unit rules score from the counted activity.
        if bulk is not None:
            if (rule.rule_type == RuleType.per_unit
                    and rule.metric in bulk):
                value = (submission.metrics or {}).get(bulk[rule.metric], 0)
                units, pts = per_unit_points(rule, value)
                if pts:
                    bd.add(PointLine(rule.id, rule.label, "auto", units, pts))
            continue

        if rule.rule_type == RuleType.per_unit and rule.metric in AUTO_METRICS:
            value = submission.bytes_added or 0
            gated = (
                submission.is_new_page
                and min_new_bytes is not None
                and (submission.page_len or 0) < min_new_bytes
            )
            units, pts = (0, 0.0) if gated else per_unit_points(rule, value)
            label = rule.label + (" (below new-article minimum)" if gated else "")
            if pts or gated:
                bd.add(PointLine(rule.id, label, "auto", units, pts))
            continue

        if rule.rule_type == RuleType.suggested_list:
            if submission.title.lower() in suggested_titles:
                bd.add(PointLine(rule.id, rule.label, "auto", 1, float(rule.points)))
            continue

        # Claims exist only in self/hybrid mode; never count them in jury
        # mode even if stale rows linger from a scoring-mode change.
        if scoring_mode == ScoringMode.jury:
            continue
        claim = claims_by_rule.get(rule.id)
        if claim is None:
            continue
        unverified_ok = bool(settings.get("unverified_claims_count", True))
        counts = (claim.status != ClaimStatus.rejected
                  and (unverified_ok or claim.status != ClaimStatus.claimed))
        if rule.rule_type in (RuleType.per_unit, RuleType.flat_bonus):
            bd.add(PointLine(rule.id, rule.label, "claimed", claim.quantity,
                             claim.effective_points if counts else 0.0,
                             status=claim.status.value))

    # ---- jury average: jury and hybrid modes -------------------------------
    if scoring_mode in (ScoringMode.jury, ScoringMode.hybrid):
        accepted = [r for r in submission.reviews
                    if r.decision == ReviewDecision.accept]
        needed = int(settings.get("min_reviews_per_submission", 1) or 1)
        if accepted and len(accepted) >= needed:
            totals = [float(r.total) for r in accepted]
            if settings.get("consensual_vote") and len(set(totals)) > 1:
                # Fountain's ConsensualVote: no agreement, no jury points.
                return bd
            avg = round(sum(totals) / len(totals), 2)
            bd.add(PointLine(None, f"Jury average ({len(accepted)} review(s))",
                             "jury", len(accepted), avg))

    return bd


def review_total(criteria: list[dict], scores: dict) -> float:
    """Server-side total of a jury mark against the campaign's review
    criteria (Fountain-style parts: radio / check / int)."""
    total = 0.0
    for part in criteria or []:
        key = part.get("key") or part.get("title")
        value = (scores or {}).get(key)
        if value is None:
            continue
        kind = part.get("type", "int")
        if kind == "radio":
            options = part.get("values", [])
            if isinstance(value, bool):  # backwards compat, like Fountain
                value = 1 if value else 0
            if isinstance(value, int) and 0 <= value < len(options):
                total += float(options[value].get("value", 0))
        elif kind == "check":
            if value is True:
                total += float(part.get("value", 0))
        elif kind == "int":
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                total += float(value)
    return round(total, 2)


# --------------------------------------------------------------------------
# Default rule presets offered in the campaign editor
# --------------------------------------------------------------------------

def default_self_assessment_rules() -> list[dict]:
    """The example rule set from the tool documentation (fully editable)."""
    A = RuleApplies.article.value
    W = RuleApplies.wikidata_item.value
    C = RuleApplies.commons_file.value
    ANY = RuleApplies.any.value
    return [
        dict(rule_type="per_unit", applies_to=A, label="Content added",
             metric="bytes_added", unit_size=1000, points=1, is_auto=True,
             params={"rounding": "nearest"}),
        dict(rule_type="threshold", applies_to=A, label="New article minimum size",
             params={"min_new_article_bytes": 3500}),
        dict(rule_type="flat_bonus", applies_to=A, label="Substantial improvement",
             metric="substantial_improvement", points=2,
             params={"min_bytes": 500}),
        dict(rule_type="suggested_list", applies_to=A,
             label="Article from the suggested list", points=10),
        dict(rule_type="flat_bonus", applies_to=A, label="Good Article",
             metric="good_article", points=25),
        dict(rule_type="per_unit", applies_to=ANY, label="Images added",
             metric="image_added", unit_size=1, points=1),
        dict(rule_type="per_unit", applies_to=ANY, label="References added",
             metric="reference_added", unit_size=1, points=1),
        dict(rule_type="flat_bonus", applies_to=W, label="New Wikidata item created",
             metric="item_created", points=3),
        dict(rule_type="per_unit", applies_to=W, label="Statements added",
             metric="statements", unit_size=5, points=1),
        dict(rule_type="per_unit", applies_to=W, label="Labels / descriptions / aliases",
             metric="labels_descriptions_aliases", unit_size=5, points=1),
        dict(rule_type="suggested_list", applies_to=W,
             label="Item from the suggested list", points=5),
        dict(rule_type="per_unit", applies_to=C, label="Depicts added",
             metric="depicts_added", unit_size=1, points=1),
        dict(rule_type="eligibility", applies_to=W, label="Topic eligibility",
             params={"any_of": ["P17=Q668", "P27=Q668", "P407=Q36236",
                                "P1412=Q36236"]}),
    ]

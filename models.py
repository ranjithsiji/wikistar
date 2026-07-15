"""WikiSTAR v2 database schema.

Design notes
------------
* Identity comes only from MediaWiki OAuth — no email / password columns.
* Roles are per-campaign (campaign_members), not global. The only global
  flag is users.is_admin.
* Points are never stored on a submission; they are derived from reviews
  (jury mode) or claims + auto-computed metrics (self-assessment mode).
  The single exception is submissions.points_override — the organizers'
  documented "final say".
* Scoring is configurable per campaign through scoring_rules rows
  (see scoring.py for rule semantics).
"""
import enum
from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------

class CampaignStatus(str, enum.Enum):
    draft = "draft"          # being configured by the organizer
    active = "active"        # approved & running — accepts submissions
    finished = "finished"    # past end date / closed — judging may continue
    archived = "archived"    # results frozen and published
    rejected = "rejected"    # refused by an admin


class ScoringMode(str, enum.Enum):
    jury = "jury"            # classic: jurors score every submission
    self_ = "self"           # participants claim their own points
    hybrid = "hybrid"        # participants claim, jury verifies/spot-checks


class MemberRole(str, enum.Enum):
    organizer = "organizer"
    jury = "jury"
    participant = "participant"


class SubmissionKind(str, enum.Enum):
    article = "article"
    wikidata_item = "wikidata_item"


class SubmissionStatus(str, enum.Enum):
    submitted = "submitted"
    accepted = "accepted"
    rejected = "rejected"


class RuleType(str, enum.Enum):
    per_unit = "per_unit"            # N points per unit_size of a metric
    flat_bonus = "flat_bonus"        # N points if a condition/claim holds
    suggested_list = "suggested_list"  # N points if page is on the suggested list
    threshold = "threshold"          # gate, e.g. new article must be >= 3500 bytes
    eligibility = "eligibility"      # topical constraint, e.g. P17=Q668


class RuleApplies(str, enum.Enum):
    article = "article"
    wikidata_item = "wikidata_item"
    any = "any"


class ReviewDecision(str, enum.Enum):
    accept = "accept"
    reject = "reject"
    needs_work = "needs_work"


class ClaimStatus(str, enum.Enum):
    claimed = "claimed"      # entered by the participant, not yet checked
    verified = "verified"    # organizer/jury confirmed as claimed
    adjusted = "adjusted"    # organizer set a different final value
    rejected = "rejected"    # counts as 0


# --------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # CentralAuth global user id ("sub" in the OAuth profile) — stable even
    # if the account is renamed.
    mw_global_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)

    memberships: Mapped[list["CampaignMember"]] = relationship(
        back_populates="user", foreign_keys="CampaignMember.user_id"
    )


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    wiki_domain: Mapped[str] = mapped_column(String(120), default="en.wikipedia.org")
    language: Mapped[str] = mapped_column(String(12), default="en")
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus), default=CampaignStatus.draft
    )
    scoring_mode: Mapped[ScoringMode] = mapped_column(
        Enum(ScoringMode), default=ScoringMode.jury
    )
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    creator: Mapped[User | None] = relationship()
    members: Mapped[list["CampaignMember"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    rules: Mapped[list["ScoringRule"]] = relationship(
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="ScoringRule.position",
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    suggested_pages: Mapped[list["SuggestedPage"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    settings_rows: Mapped[list["CampaignSetting"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )

    @property
    def effective_settings(self) -> dict:
        """Registry defaults merged with this campaign's overrides."""
        from settings_registry import defaults

        merged = defaults()
        for row in self.settings_rows:
            merged[row.key] = row.value
        return merged

    def set_settings(self, overrides: dict) -> None:
        """Replace the stored overrides (already validated)."""
        self.settings_rows = [
            CampaignSetting(key=k, value=v) for k, v in overrides.items()
        ]


class CampaignSetting(Base):
    """One overridden setting of a campaign. Known keys, types and
    defaults are declared in settings_registry.SETTING_DEFS."""

    __tablename__ = "campaign_settings"
    __table_args__ = (
        UniqueConstraint("campaign_id", "key", name="uq_campaign_setting"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(80))
    value: Mapped[dict | list | str | int | bool | None] = mapped_column(JSON)

    campaign: Mapped[Campaign] = relationship(back_populates="settings_rows")


class CampaignMember(Base):
    """Per-campaign role. A user may hold several roles in one campaign
    (e.g. organizer + participant) and different roles across campaigns."""

    __tablename__ = "campaign_members"
    __table_args__ = (
        UniqueConstraint("campaign_id", "user_id", "role", name="uq_member_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole))
    added_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    added_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    campaign: Mapped[Campaign] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="memberships", foreign_keys=[user_id])


class ScoringRule(Base):
    """One configurable scoring rule of a campaign.

    Interpretation by rule_type (see scoring.py):
      per_unit       — `points` per `unit_size` of `metric`
                       (metrics: bytes_added [auto], statements,
                        labels_descriptions_aliases, references [claimed])
      flat_bonus     — `points` once per submission when claimed/detected
                       (metric holds the trigger: substantial_improvement,
                        good_article, item_created, ...)
      suggested_list — `points` when the submission title is on the
                       campaign's suggested_pages list [auto]
      threshold      — no points; params define a gate, e.g.
                       {"min_new_article_bytes": 3500}
      eligibility    — no points; params document a topical constraint,
                       e.g. {"any_of": ["P17=Q668", "P407=Q36236"]}
    """

    __tablename__ = "scoring_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    rule_type: Mapped[RuleType] = mapped_column(Enum(RuleType))
    applies_to: Mapped[RuleApplies] = mapped_column(
        Enum(RuleApplies), default=RuleApplies.any
    )
    label: Mapped[str] = mapped_column(String(255))
    metric: Mapped[str | None] = mapped_column(String(50))
    unit_size: Mapped[int] = mapped_column(Integer, default=1)
    points: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    max_units: Mapped[int | None] = mapped_column(Integer)  # optional cap
    # True when the engine computes the value from wiki data itself;
    # False when the participant must claim it (self-assessment).
    is_auto: Mapped[bool] = mapped_column(Boolean, default=False)
    params: Mapped[dict | None] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    campaign: Mapped[Campaign] = relationship(back_populates="rules")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("campaign_id", "user_id", "title", name="uq_submission"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[SubmissionKind] = mapped_column(
        Enum(SubmissionKind), default=SubmissionKind.article
    )
    title: Mapped[str] = mapped_column(String(500))  # article title or QID
    wiki_domain: Mapped[str] = mapped_column(String(120))
    # Snapshot fetched from the MediaWiki API (refreshable):
    page_id: Mapped[int | None] = mapped_column(BigInteger)
    base_rev_id: Mapped[int | None] = mapped_column(BigInteger)
    current_rev_id: Mapped[int | None] = mapped_column(BigInteger)
    page_len: Mapped[int | None] = mapped_column(Integer)
    bytes_added: Mapped[int] = mapped_column(Integer, default=0)
    is_new_page: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_fetched_at: Mapped[datetime | None] = mapped_column(DateTime)

    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus), default=SubmissionStatus.submitted
    )
    # Organizers' final say: overrides every computed value when set.
    points_override: Mapped[float | None] = mapped_column(Numeric(8, 2))
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    campaign: Mapped[Campaign] = relationship(back_populates="submissions")
    user: Mapped[User] = relationship()
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )
    claims: Mapped[list["Claim"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )

    @property
    def url(self) -> str:
        return f"https://{self.wiki_domain}/wiki/{self.title.replace(' ', '_')}"


class Review(Base):
    """A jury member's verdict on one submission — one row per juror."""

    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("submission_id", "reviewer_id", name="uq_review"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), index=True
    )
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    scores: Mapped[dict | None] = mapped_column(JSON)  # per-criterion detail
    total: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    decision: Mapped[ReviewDecision] = mapped_column(
        Enum(ReviewDecision), default=ReviewDecision.needs_work
    )
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    submission: Mapped[Submission] = relationship(back_populates="reviews")
    reviewer: Mapped[User] = relationship()


class Claim(Base):
    """Self-assessment: a participant claims points under one scoring rule.

    points_claimed is always computed server-side from the rule and the
    quantity. Organizers verify, adjust (points_final) or reject.
    """

    __tablename__ = "claims"
    __table_args__ = (
        UniqueConstraint("submission_id", "rule_id", name="uq_claim"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), index=True
    )
    rule_id: Mapped[int] = mapped_column(ForeignKey("scoring_rules.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    points_claimed: Mapped[float] = mapped_column(Numeric(8, 2), default=0)
    evidence_url: Mapped[str | None] = mapped_column(String(1000))
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus), default=ClaimStatus.claimed
    )
    points_final: Mapped[float | None] = mapped_column(Numeric(8, 2))
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    submission: Mapped[Submission] = relationship(back_populates="claims")
    rule: Mapped[ScoringRule] = relationship()

    @property
    def effective_points(self) -> float:
        if self.status == ClaimStatus.rejected:
            return 0.0
        if self.points_final is not None:
            return float(self.points_final)
        return float(self.points_claimed)


class SuggestedPage(Base):
    """Suggested articles / Wikidata items that earn a list bonus."""

    __tablename__ = "suggested_pages"
    __table_args__ = (
        UniqueConstraint("campaign_id", "kind", "title", name="uq_suggested"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[SubmissionKind] = mapped_column(
        Enum(SubmissionKind), default=SubmissionKind.article
    )
    title: Mapped[str] = mapped_column(String(500))
    note: Mapped[str | None] = mapped_column(String(500))

    campaign: Mapped[Campaign] = relationship(back_populates="suggested_pages")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

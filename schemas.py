"""Pydantic request/response schemas (API contract)."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from models import (
    CampaignStatus,
    ClaimStatus,
    MemberRole,
    ReviewDecision,
    RuleApplies,
    RuleType,
    ScoringMode,
    SubmissionKind,
    SubmissionStatus,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- users ----------------------------------------------------------------

class UserOut(ORMModel):
    id: int
    username: str
    is_admin: bool


# ---- scoring rules ---------------------------------------------------------

class RuleIn(BaseModel):
    id: int | None = None  # present on update: keep/refresh an existing rule
    rule_type: RuleType
    applies_to: RuleApplies = RuleApplies.any
    label: str = Field(min_length=1, max_length=255)
    metric: str | None = None
    unit_size: int = Field(default=1, ge=1)
    points: float = 0
    max_units: int | None = Field(default=None, ge=1)
    is_auto: bool = False
    params: dict | None = None
    active: bool = True


class RuleOut(RuleIn, ORMModel):
    id: int
    position: int


# ---- campaigns -------------------------------------------------------------

class CampaignIn(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    slug: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9_-]*$",
                             max_length=80)
    description: str | None = None
    language: str = "en"
    wiki_domain: str | None = None  # derived from language when omitted
    start_date: date
    end_date: date
    scoring_mode: ScoringMode = ScoringMode.jury
    status: CampaignStatus | None = None  # organizer lifecycle changes on update
    settings: dict = {}  # validated against settings_registry
    rules: list[RuleIn] = []
    jury_usernames: list[str] = []
    suggested_articles: list[str] = []
    suggested_items: list[str] = []


class MemberOut(ORMModel):
    id: int
    role: MemberRole
    user: UserOut


class MemberAddIn(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    role: MemberRole


class CampaignSummary(ORMModel):
    id: int
    slug: str
    name: str
    description: str | None
    language: str
    wiki_domain: str
    start_date: date
    end_date: date
    status: CampaignStatus
    scoring_mode: ScoringMode
    submission_count: int = 0
    participant_count: int = 0
    review_count: int = 0


class CampaignDetail(CampaignSummary):
    settings: dict = {}  # effective (defaults + overrides)
    created_by_username: str | None = None
    rules: list[RuleOut] = []
    members: list[MemberOut] = []
    suggested_articles: list[str] = []
    suggested_items: list[str] = []
    my_roles: list[MemberRole] = []


# ---- submissions -----------------------------------------------------------

class SubmissionIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    kind: SubmissionKind = SubmissionKind.article
    # Wiki language of the article; honoured only in multi-language
    # campaigns (otherwise the campaign's wiki always applies).
    language: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9-]{1,11}$")


class PointLineOut(BaseModel):
    rule_id: int | None
    label: str
    source: str
    quantity: float
    points: float
    status: str = ""


class ReviewOut(ORMModel):
    id: int
    reviewer: UserOut
    scores: dict | None
    total: float
    decision: ReviewDecision
    comment: str | None
    updated_at: datetime


class ClaimIn(BaseModel):
    rule_id: int
    quantity: int = Field(default=1, ge=0)
    evidence_url: str | None = Field(default=None, max_length=1000)
    note: str | None = None


class ClaimOut(ORMModel):
    id: int
    rule_id: int
    quantity: int
    points_claimed: float
    evidence_url: str | None
    note: str | None
    status: ClaimStatus
    points_final: float | None


class SubmissionOut(ORMModel):
    id: int
    campaign_id: int
    kind: SubmissionKind
    title: str
    wiki_domain: str
    url: str
    user: UserOut
    page_len: int | None
    bytes_added: int
    is_new_page: bool
    status: SubmissionStatus
    points_override: float | None
    submitted_at: datetime
    reviews: list[ReviewOut] = []
    claims: list[ClaimOut] = []
    points: float = 0
    breakdown: list[PointLineOut] = []


# ---- reviews / claims ------------------------------------------------------

class ReviewIn(BaseModel):
    scores: dict | None = None
    total: float = 0
    decision: ReviewDecision
    comment: str | None = None


class ClaimModeration(BaseModel):
    status: ClaimStatus
    points_final: float | None = None
    note: str | None = None


class SubmissionModerationIn(BaseModel):
    status: SubmissionStatus | None = None
    points_override: float | None = None
    clear_override: bool = False


# ---- leaderboard / statistics ----------------------------------------------

class LeaderboardRow(BaseModel):
    rank: int
    user: UserOut
    submission_count: int
    points: float


class CampaignStats(BaseModel):
    submissions: int
    participants: int
    reviews: int
    claims: int
    pending_claims: int
    unreviewed_submissions: int
    total_points: float
    total_bytes_added: int
    new_pages: int
    by_kind: dict[str, int]
    by_status: dict[str, int]
    timeline: list[dict]        # [{date, submissions}]
    top_contributors: list[LeaderboardRow]

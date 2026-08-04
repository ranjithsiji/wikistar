"""Pydantic request/response schemas (API contract)."""
from datetime import date, datetime, timezone
from typing import Annotated

from pydantic import (BaseModel, ConfigDict, Field, PlainSerializer,
                      field_validator)


def _as_utc(value: datetime) -> str:
    """Serialize a timestamp so the browser cannot read it as local time.

    Timestamps are stored UTC in a plain DateTime column, which MySQL hands
    back naive. isoformat() then omits any offset, and `new Date(...)` in
    the browser reads an offset-less string as *local* time — so a reader
    in UTC+5:30 saw every timestamp shifted by 5.5 hours, and a row
    recalculated a moment ago still read "6 h ago". Stamp the UTC the
    values already carry.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


UtcDatetime = Annotated[datetime, PlainSerializer(_as_utc, return_type=str)]

from domain.models import (
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

class SuggestedItemIn(BaseModel):
    qid: str = Field(min_length=1, max_length=500)
    section: str = Field(default="", max_length=255)


class SuggestedItemOut(BaseModel):
    qid: str
    section: str = ""


class CampaignIn(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    # Mandatory and strictly [a-z0-9-]: the slug is the campaign's public
    # URL, so it is the organizer's deliberate choice rather than
    # something derived from the name. Underscores are not accepted.
    slug: str = Field(min_length=1, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
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
    coordinator_usernames: list[str] = []  # extra organizers; creator always stays
    suggested_articles: list[str] = []
    # Accepts plain "Q42" strings or {"qid": "Q42", "section": "Rivers"};
    # normalised to SuggestedItemIn by the validator.
    suggested_items: list[SuggestedItemIn] = []

    @field_validator("suggested_items", mode="before")
    @classmethod
    def _coerce_items(cls, value):
        if not isinstance(value, list):
            return value
        return [{"qid": v} if isinstance(v, str) else v for v in value]


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
    suggested_items: list[SuggestedItemOut] = []
    my_roles: list[MemberRole] = []


# ---- submissions -----------------------------------------------------------

class SubmissionIn(BaseModel):
    # Optional for the bulk kinds (wikidata_edits / commons_edits), which
    # carry a canonical title; required for page submissions (router-checked).
    title: str = Field(default="", max_length=500)
    kind: SubmissionKind = SubmissionKind.article
    # Wiki language of the article; honoured only in multi-language
    # campaigns (otherwise the campaign's wiki always applies).
    language: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9-]{1,11}$")
    # Coordinators may submit on behalf of a participant; ignored when it
    # names the submitter themselves, forbidden for everyone else.
    username: str | None = Field(default=None, max_length=255)


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
    updated_at: UtcDatetime


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
    wikidata_qid: str | None = None    # article's connected item
    metrics: dict | None = None    # bulk kinds: counted activity
    status: SubmissionStatus
    moderation_note: str | None = None
    points_override: float | None
    submitted_at: UtcDatetime
    # When the wiki data behind this submission was last fetched — for bulk
    # submissions that is when its counts were last recalculated.
    metadata_fetched_at: UtcDatetime | None = None
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
    moderation_note: str | None = None


# ---- leaderboard / statistics ----------------------------------------------

class LeaderboardRow(BaseModel):
    rank: int
    user: UserOut
    submission_count: int
    points: float
    bytes_added: int = 0


class CampaignStats(BaseModel):
    submissions: int
    participants: int
    languages: int
    reviews: int
    claims: int
    pending_claims: int
    unreviewed_submissions: int
    total_points: float
    total_bytes_added: int
    new_pages: int
    by_kind: dict[str, int]
    by_status: dict[str, int]
    by_language: dict[str, int]
    timeline: list[dict]        # [{date, submissions}]
    top_contributors: list[LeaderboardRow]

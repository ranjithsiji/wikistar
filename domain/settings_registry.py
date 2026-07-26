"""Registry of per-campaign settings.

Every setting a campaign can carry is declared here with its type,
default, label and category. The campaign_settings table stores only
overrides; Campaign.effective_settings merges them over the defaults.
The frontend renders the settings form from GET /api/meta, so adding a
setting here is enough to surface it in the UI.
"""
from typing import Any

SETTING_DEFS: dict[str, dict[str, Any]] = {
    # -- participation -------------------------------------------------------
    "jury_can_submit": dict(
        type="bool", default=False, category="participation",
        label="Jury members may submit",
        help="Allow jurors to take part with their own submissions."),
    "max_submissions_per_user": dict(
        type="int", default=0, min=0, category="participation",
        label="Max submissions per participant",
        help="0 means unlimited."),
    "allow_articles": dict(
        type="bool", default=True, category="participation",
        label="Accept Wikipedia articles"),
    "multi_language": dict(
        type="bool", default=False, category="participation",
        label="Multi-language campaign",
        help="Participants may submit articles from any language "
             "Wikipedia, choosing the language per submission. Off: only "
             "the campaign's wiki is accepted."),
    "allow_wikidata_items": dict(
        type="bool", default=False, category="participation",
        label="Accept Wikidata items"),
    "allow_commons_files": dict(
        type="bool", default=False, category="participation",
        label="Accept Wikimedia Commons files",
        help="e.g. adding depicts statements to images."),
    "allow_submissions_after_end": dict(
        type="bool", default=False, category="participation",
        label="Accept submissions after the end date",
        help="e.g. to register Good Article nominations decided later."),
    "max_wikidata_edits_auto": dict(
        type="int", default=50, min=0, category="participation",
        label="Max Wikidata edits for automatic scoring",
        help="Bulk Wikidata submissions by users with more edits than this "
             "in the campaign period (e.g. QuickStatements/OpenRefine runs) "
             "are not scored automatically — the coordinator reviews the "
             "contributions and enters the points manually. 0 disables "
             "the cap."),
    "max_commons_uploads_auto": dict(
        type="int", default=100, min=0, category="participation",
        label="Max Commons uploads for automatic scoring",
        help="Bulk Commons submissions with more uploads or file edits "
             "than this are not scored automatically — the coordinator "
             "enters the points manually. 0 disables the cap."),

    # -- eligibility (Fountain-style article rules) ---------------------------
    "require_page_created_during_campaign": dict(
        type="bool", default=False, category="eligibility",
        label="Article must be created during the campaign",
        help="Submissions of pages that existed before the start date are "
             "rejected (checked against the page history)."),
    "min_article_bytes": dict(
        type="int", default=0, min=0, category="eligibility",
        label="Minimum article size (bytes)",
        help="0 disables the check."),
    "submitter_registered_after": dict(
        type="str", default="", category="eligibility",
        label="Submitter account created after (YYYY-MM-DD)",
        help="Restrict to newcomers; empty disables the check."),
    "submitter_must_be_creator": dict(
        type="bool", default=False, category="eligibility",
        label="Submitter must be the article's creator",
        help="Checked against the first revision of the page."),

    # -- jury review ---------------------------------------------------------
    "min_reviews_per_submission": dict(
        type="int", default=1, min=1, category="jury",
        label="Reviews needed before points count",
        help="Jury mode: a submission scores only once this many jurors "
             "accepted it."),
    "consensual_vote": dict(
        type="bool", default=False, category="jury",
        label="Consensual vote",
        help="Jury mode: points count only when every review agrees on the "
             "same total."),
    "anonymous_reviews": dict(
        type="bool", default=False, category="jury",
        label="Hidden marks",
        help="Jurors see only their own marks; points are hidden from "
             "everyone but organizers until revealed."),
    "jury_criteria": dict(
        type="json", json_shape="list", default=[], category="jury",
        label="Review criteria",
        help='Fountain-style parts, e.g. [{"key": "quality", "title": '
             '"Quality", "type": "radio", "values": [{"title": "ok", '
             '"value": 1}, {"title": "great", "value": 2}]}, {"key": '
             '"sourced", "title": "Well sourced", "type": "check", '
             '"value": 1}, {"key": "bonus", "title": "Bonus", "type": '
             '"int"}]. The review total is computed server-side.'),

    # -- self-assessment -----------------------------------------------------
    "unverified_claims_count": dict(
        type="bool", default=True, category="self_assessment",
        label="Unverified claims count towards the score",
        help="If off, claims earn points only after organizer verification."),
    "claims_editable_after_end": dict(
        type="bool", default=True, category="self_assessment",
        label="Claims stay editable after the end date",
        help="Until the campaign is archived."),

    # -- template ------------------------------------------------------------
    "auto_add_template": dict(
        type="bool", default=False, category="template",
        label="Automatically add template",
        help="On every article submission, write the campaign template to "
             "the wiki with the submitter's account. Off: nothing is "
             "written. Needs an OAuth consumer with edit rights."),
    "template_name": dict(
        type="str", default="", category="template",
        label="Template name",
        help='Without braces, e.g. "Wiki Asian Month 2025 talk".'),
    "template_placement": dict(
        type="str", default="talk", choices=["talk", "article"],
        category="template",
        label="Template placement",
        help="talk: on the article's talk page (default); "
             "article: at the top of the article itself."),

    # -- display -------------------------------------------------------------
    "logo": dict(
        type="str", default="", category="display",
        label="Campaign logo (Commons file)",
        help='File name on Wikimedia Commons, e.g. '
             '"File:Wiki Loves Earth Logo.svg". Shown on the campaign page.'),
    "campaign_page_url": dict(
        type="str", default="", category="display",
        label="Campaign page link",
        help="URL of the campaign's page on your wiki or Meta-Wiki."),
    "show_leaderboard": dict(
        type="bool", default=True, category="display",
        label="Public leaderboard"),
    "show_leaderboard_podium": dict(
        type="bool", default=True, category="display",
        label="Podium on the leaderboard",
        help="Show the top-3 podium above the standings table. Turn off "
             "to go straight to the table."),
    "show_points_during_campaign": dict(
        type="bool", default=True, category="display",
        label="Show points while the campaign runs"),
}


def defaults() -> dict[str, Any]:
    return {key: spec["default"] for key, spec in SETTING_DEFS.items()}


def validate_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    """Type-check incoming settings; unknown keys and wrong types are
    rejected with ValueError. Returns only values differing from default."""
    clean: dict[str, Any] = {}
    for key, value in (overrides or {}).items():
        spec = SETTING_DEFS.get(key)
        if spec is None:
            raise ValueError(f"Unknown setting: {key}")
        kind = spec["type"]
        if kind == "bool":
            if not isinstance(value, bool):
                raise ValueError(f"Setting {key} must be a boolean")
        elif kind == "int":
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"Setting {key} must be an integer")
            low, high = spec.get("min"), spec.get("max")
            if low is not None and value < low:
                raise ValueError(f"Setting {key} must be at least {low}")
            if high is not None and value > high:
                raise ValueError(f"Setting {key} must be at most {high}")
        elif kind == "str":
            if not isinstance(value, str):
                raise ValueError(f"Setting {key} must be a string")
            choices = spec.get("choices")
            if choices and value not in choices:
                raise ValueError(
                    f"Setting {key} must be one of: {', '.join(choices)}")
        elif kind == "json":
            shape = spec.get("json_shape")
            if shape == "list":
                if not isinstance(value, list):
                    raise ValueError(f"Setting {key} must be a JSON list")
            elif shape == "object":
                if not isinstance(value, dict):
                    raise ValueError(f"Setting {key} must be a JSON object")
            elif not isinstance(value, (list, dict)):
                raise ValueError(f"Setting {key} must be a JSON list/object")
        if value != spec["default"]:
            clean[key] = value
    return clean

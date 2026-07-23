"""Campaign approval rights, following the Fountain model.

Who may approve (publish) a campaign:
  * a WikiSTAR site admin — always;
  * a global sysop / steward — always;
  * jury mode      — a sysop on the campaign's target wiki
                     (that sysop can also see the draft);
  * multi-language — a sysop on ANY project (submissions come from
                     every wiki, so no single target wiki exists);
  * self / hybrid  — a sysop on ANY Wikipedia project.

Creators who hold the required right get their campaign approved
automatically at creation time.
"""
from integrations import mediawiki
from domain.models import Campaign, ScoringMode, User


def can_approve_campaign(user: User, campaign: Campaign) -> tuple[bool, str]:
    """Returns (allowed, reason). Never raises: API failures deny."""
    if user.is_admin:
        return True, "site_admin"
    try:
        domains = mediawiki.fetch_sysop_wikis(user.username)
    except Exception:
        return False, "rights_check_failed"
    if "*" in domains:
        return True, "global_sysop_or_steward"

    # Multi-language campaigns have no single target wiki: any sysop may
    # approve, regardless of scoring mode.
    if campaign.effective_settings.get("multi_language"):
        if domains:
            return True, f"sysop_on_{sorted(domains)[0]}"
        return False, "requires_sysop_on_any_project"

    if campaign.scoring_mode == ScoringMode.jury:
        if campaign.wiki_domain in domains:
            return True, f"sysop_on_{campaign.wiki_domain}"
        return False, f"requires_sysop_on_{campaign.wiki_domain}"

    # self-assessment / hybrid: an admin on any Wikipedia project will do
    wikipedias = sorted(d for d in domains if d.endswith("wikipedia.org"))
    if wikipedias:
        return True, f"sysop_on_{wikipedias[0]}"
    return False, "requires_sysop_on_any_wikipedia"

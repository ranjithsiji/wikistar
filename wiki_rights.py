"""Campaign approval rights, following the Fountain model.

Who may approve (publish) a campaign:
  * a WikiSTAR site admin — always;
  * a global sysop / steward — always;
  * jury mode      — a sysop on the campaign's target wiki;
  * self / hybrid  — a sysop on ANY Wikipedia project.

Creators who hold the required right get their campaign approved
automatically at creation time.
"""
import mediawiki
from models import Campaign, ScoringMode, User


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

    if campaign.scoring_mode == ScoringMode.jury:
        if campaign.wiki_domain in domains:
            return True, f"sysop_on_{campaign.wiki_domain}"
        return False, f"requires_sysop_on_{campaign.wiki_domain}"

    # self-assessment / hybrid: an admin on any Wikipedia project will do
    wikipedias = sorted(d for d in domains if d.endswith("wikipedia.org"))
    if wikipedias:
        return True, f"sysop_on_{wikipedias[0]}"
    return False, "requires_sysop_on_any_wikipedia"

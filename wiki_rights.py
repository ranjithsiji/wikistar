"""
Helper to check user rights on a given Wikipedia/Wikimedia project via the MediaWiki API.
"""
import requests


def get_wiki_domain(editathon) -> str:
    """Return the wiki API base URL for a given editathon."""
    if editathon.wiki_domain:
        domain = editathon.wiki_domain
    elif editathon.language:
        domain = f"{editathon.language}.wikipedia.org"
    else:
        domain = "en.wikipedia.org"
    return domain


def get_user_groups(username: str, wiki_domain: str) -> list:
    """
    Query the MediaWiki API and return the list of groups the user belongs to.
    Returns an empty list on any error.
    """
    url = f"https://{wiki_domain}/w/api.php"
    params = {
        "action": "query",
        "list": "users",
        "ususers": username,
        "usprop": "groups|rights",
        "format": "json"
    }
    try:
        resp = requests.get(url, params=params, timeout=8, headers={
            "User-Agent": "WikiSTAR/1.0 (https://wikistar.toolforge.org)"
        })
        data = resp.json()
        users = data.get("query", {}).get("users", [])
        if users and "invalid" not in users[0] and "missing" not in users[0]:
            return users[0].get("groups", [])
    except Exception as e:
        print(f"[wiki_rights] Error checking {username} on {wiki_domain}: {e}")
    return []


def is_sysop_on_wiki(username: str, wiki_domain: str) -> bool:
    """Return True if the user has the 'sysop' group on the given wiki."""
    groups = get_user_groups(username, wiki_domain)
    return "sysop" in groups


def can_approve_campaign(user, editathon) -> tuple[bool, str]:
    """
    Determine if a user can approve a campaign.
    Rules:
      1. App-level admin can always approve.
      2. A sysop on the editathon's target wiki can approve.
    Returns (allowed: bool, reason: str).
    """
    if user.role == "admin":
        return True, "global_admin"

    wiki_domain = get_wiki_domain(editathon)
    if is_sysop_on_wiki(user.username, wiki_domain):
        return True, f"sysop_on_{wiki_domain}"

    return False, f"not_sysop_on_{wiki_domain}"

"""Allowlist for Wikimedia wiki hostnames.

`wiki_domain` (and the language that derives it) reaches the MediaWiki
client, which builds ``https://{domain}/w/api.php`` and — for the
auto-template feature — sends the *submitter's* OAuth token to that host.
An unvalidated domain therefore allows SSRF to arbitrary/internal hosts
and, worse, exfiltration of participant access tokens to an attacker's
server. Every domain that enters the system is checked against this
allowlist first.
"""
import re

# Public Wikimedia content projects. A leading subdomain (language code or
# "www"/"commons"/"meta"/…) is optional; the second-level name must be one
# of the known project families. Anchored, lowercase-only, no port/path.
_WIKIMEDIA_DOMAIN_RE = re.compile(
    r"^(?:[a-z0-9-]+\.)?"
    r"(?:wikipedia|wiktionary|wikibooks|wikinews|wikiquote|wikisource"
    r"|wikiversity|wikivoyage|wikidata|wikimedia|mediawiki|wikifunctions)"
    r"\.org$"
)

# Upper bound so a pathological string never reaches the regex engine.
MAX_DOMAIN_LEN = 80


def is_wikimedia_domain(domain: str | None) -> bool:
    """True when `domain` is a bare Wikimedia wiki hostname we may call."""
    if not domain or len(domain) > MAX_DOMAIN_LEN:
        return False
    return bool(_WIKIMEDIA_DOMAIN_RE.match(domain))


def normalize_domain(domain: str) -> str:
    """Lowercase/strip a domain for comparison and storage."""
    return (domain or "").strip().lower()

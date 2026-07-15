"""Read-only MediaWiki / Wikidata API client (httpx, no auth needed).

Used to verify submissions instead of trusting user input:
  * does the page exist, its size and current revision
  * how many bytes the participant added during the campaign window
  * whether the participant created the page during the window
"""
from dataclasses import dataclass
from datetime import date, datetime, time, timezone

import httpx

from auth import USER_AGENT

TIMEOUT = 15.0


def api_url(domain: str) -> str:
    return f"https://{domain}/w/api.php"


def _client() -> httpx.Client:
    return httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)


def _iso(d: date, end: bool = False) -> str:
    t = time(23, 59, 59) if end else time(0, 0, 0)
    return datetime.combine(d, t, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class PageMetadata:
    exists: bool = False
    page_id: int | None = None
    page_len: int | None = None
    current_rev_id: int | None = None
    base_rev_id: int | None = None
    bytes_added: int = 0
    is_new_page: bool = False


def fetch_page_metadata(
    domain: str, title: str, username: str, start: date, end: date
) -> PageMetadata:
    """Fetch page info and the participant's byte delta within [start, end].

    bytes_added sums max(0, size_after - size_before) over the user's
    revisions inside the window. Network errors raise httpx.HTTPError —
    callers decide whether that is fatal (submission still accepted,
    metadata refreshable later).
    """
    meta = PageMetadata()
    with _client() as client:
        info = client.get(api_url(domain), params={
            "action": "query", "format": "json", "formatversion": 2,
            "prop": "info", "titles": title,
        }).json()
        page = info["query"]["pages"][0]
        if page.get("missing"):
            return meta
        meta.exists = True
        meta.page_id = page["pageid"]
        meta.page_len = page.get("length")
        meta.current_rev_id = page.get("lastrevid")

        # All revisions inside the window (oldest -> newest), plus the one
        # just before it to know the starting size.
        revs: list[dict] = []
        params = {
            "action": "query", "format": "json", "formatversion": 2,
            "prop": "revisions", "pageids": meta.page_id,
            "rvprop": "ids|timestamp|user|size",
            "rvstart": _iso(start), "rvend": _iso(end, end=True),
            "rvdir": "newer", "rvlimit": "max",
        }
        while True:
            data = client.get(api_url(domain), params=params).json()
            pages = data.get("query", {}).get("pages", [])
            if pages:
                revs.extend(pages[0].get("revisions", []))
            cont = data.get("continue")
            if not cont:
                break
            params.update(cont)

        base_size = 0
        if revs:
            meta.base_rev_id = revs[0].get("parentid") or None
            if meta.base_rev_id:
                base = client.get(api_url(domain), params={
                    "action": "query", "format": "json", "formatversion": 2,
                    "prop": "revisions", "revids": meta.base_rev_id,
                    "rvprop": "size",
                }).json()
                base_pages = base.get("query", {}).get("pages", [])
                if base_pages and base_pages[0].get("revisions"):
                    base_size = base_pages[0]["revisions"][0].get("size", 0)
            else:
                meta.is_new_page = revs[0].get("user") == username

        prev_size = base_size
        added = 0
        for rev in revs:
            size = rev.get("size", prev_size)
            if rev.get("user") == username:
                added += max(0, size - prev_size)
            prev_size = size
        meta.bytes_added = added
    return meta

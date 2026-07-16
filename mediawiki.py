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
    creator: str | None = None
    created_at: datetime | None = None


_SYSOP_CACHE: dict[str, tuple[float, set[str]]] = {}
_SYSOP_CACHE_TTL = 300.0  # seconds


def fetch_sysop_wikis(username: str) -> set[str]:
    """Domains where the user holds local sysop rights, resolved through
    CentralAuth (meta.wikimedia.org globaluserinfo), exactly like
    Fountain's GetSysopWikis. Global sysops and stewards yield "*".
    Results are cached briefly; failures raise httpx.HTTPError."""
    import time

    cached = _SYSOP_CACHE.get(username)
    if cached and cached[0] > time.monotonic():
        return cached[1]

    with _client() as client:
        data = client.get(api_url("meta.wikimedia.org"), params={
            "action": "query", "format": "json", "formatversion": 2,
            "meta": "globaluserinfo", "guiuser": username,
            "guiprop": "merged|groups",
        }).json()
    info = data.get("query", {}).get("globaluserinfo", {})
    domains: set[str] = set()
    for wiki in info.get("merged", []):
        if "sysop" in (wiki.get("groups") or []):
            url = wiki.get("url", "")
            domains.add(url.removeprefix("https://").removeprefix("http://"))
    if {"global-sysop", "steward"} & set(info.get("groups") or []):
        domains.add("*")
    _SYSOP_CACHE[username] = (time.monotonic() + _SYSOP_CACHE_TTL, domains)
    return domains


def fetch_sitelinks(qids: list[str], languages: list[str]) -> dict[str, dict]:
    """Wikidata sitelinks + label for the given items, restricted to the
    given wiki languages. Returns {qid: {"label": str|None,
    "label_en": str|None, "links": {lang: title}}}. Network errors raise
    httpx.HTTPError."""
    result: dict[str, dict] = {}
    if not qids:
        return result
    sites = [f"{lang.replace('-', '_')}wiki" for lang in languages]
    with _client() as client:
        for start in range(0, len(qids), 50):  # API limit: 50 ids per call
            chunk = qids[start:start + 50]
            data = client.get(api_url("www.wikidata.org"), params={
                "action": "wbgetentities", "format": "json",
                "ids": "|".join(chunk),
                "props": "sitelinks|labels",
                "sitefilter": "|".join(sites),
                # "mul" holds Wikidata's default-for-all-languages label.
                "languages": "|".join(languages) + "|en|mul",
            }).json()
            for qid, entity in (data.get("entities") or {}).items():
                if "missing" in entity:
                    continue
                labels = entity.get("labels") or {}
                label_en = (labels.get("en") or labels.get("mul") or {}).get("value")
                label = next((labels[lang]["value"] for lang in languages
                              if lang in labels), label_en)
                links = {}
                sitelinks = entity.get("sitelinks") or {}
                for lang in languages:
                    site = f"{lang.replace('-', '_')}wiki"
                    if site in sitelinks:
                        links[lang] = sitelinks[site]["title"]
                result[qid] = {"label": label, "label_en": label_en,
                               "links": links}
    return result


def fetch_user_registration(domain: str, username: str) -> datetime | None:
    """Account registration timestamp on the given wiki, or None."""
    with _client() as client:
        data = client.get(api_url(domain), params={
            "action": "query", "format": "json", "formatversion": 2,
            "list": "users", "ususers": username, "usprop": "registration",
        }).json()
        users = data.get("query", {}).get("users", [])
        reg = users[0].get("registration") if users else None
        if not reg:
            return None
        return datetime.strptime(reg, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc)


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)


def _first_revision(client: httpx.Client, domain: str, page_id: int) -> dict:
    data = client.get(api_url(domain), params={
        "action": "query", "format": "json", "formatversion": 2,
        "prop": "revisions", "pageids": page_id,
        "rvprop": "timestamp|user", "rvdir": "newer", "rvlimit": 1,
    }).json()
    pages = data.get("query", {}).get("pages", [])
    if pages and pages[0].get("revisions"):
        return pages[0]["revisions"][0]
    return {}


def fetch_article_details(domain: str, title: str) -> dict | None:
    """Live per-article facts for the participant popup: size, word count,
    creation/last-edit dates and the connected Wikidata item. Returns None
    for a missing page; network errors raise httpx.HTTPError."""
    with _client() as client:
        data = client.get(api_url(domain), params={
            "action": "query", "format": "json", "formatversion": 2,
            "prop": "info|pageprops", "ppprop": "wikibase_item",
            "titles": title,
        }).json()
        page = data["query"]["pages"][0]
        if page.get("missing"):
            return None
        first = _first_revision(client, domain, page["pageid"])
        extract = client.get(api_url(domain), params={
            "action": "query", "format": "json", "formatversion": 2,
            "prop": "extracts", "explaintext": 1, "exlimit": 1,
            "titles": title,
        }).json()
        text = extract["query"]["pages"][0].get("extract") or ""
    return {
        "bytes": page.get("length"),
        "words": len(text.split()),
        "created_at": _parse_ts(first.get("timestamp")),
        "last_updated": _parse_ts(page.get("touched")),
        "qid": (page.get("pageprops") or {}).get("wikibase_item"),
    }


def fetch_wikidata_details(qid: str) -> dict | None:
    """Label, size and dates of one Wikidata item, or None if missing."""
    domain = "www.wikidata.org"
    with _client() as client:
        data = client.get(api_url(domain), params={
            "action": "query", "format": "json", "formatversion": 2,
            "prop": "info", "titles": qid,
        }).json()
        page = data["query"]["pages"][0]
        if page.get("missing") or page.get("invalid"):
            return None
        first = _first_revision(client, domain, page["pageid"])
        # "mul" holds the default-for-all-languages label Wikidata uses
        # when no language-specific one exists.
        entity = client.get(api_url(domain), params={
            "action": "wbgetentities", "format": "json", "ids": qid,
            "props": "labels", "languages": "en|mul",
        }).json().get("entities", {}).get(qid, {})
        labels = entity.get("labels") or {}
        label = (labels.get("en") or labels.get("mul")
                 or next(iter(labels.values()), {})).get("value")
    return {
        "qid": qid.upper(),
        "label": label,
        "bytes": page.get("length"),
        "created_at": _parse_ts(first.get("timestamp")),
        "last_updated": _parse_ts(page.get("touched")),
    }


def fetch_commons_details(title: str) -> dict | None:
    """Size, uploader and upload date of one Commons file, or None."""
    with _client() as client:
        data = client.get(api_url("commons.wikimedia.org"), params={
            "action": "query", "format": "json", "formatversion": 2,
            "prop": "imageinfo", "iiprop": "timestamp|user|size|url",
            "iilimit": "max", "titles": title,
        }).json()
        page = data["query"]["pages"][0]
        infos = page.get("imageinfo") or []
        if page.get("missing") or not infos:
            return None
    latest, oldest = infos[0], infos[-1]  # imageinfo is newest-first
    return {
        "size": latest.get("size"),
        "width": latest.get("width"),
        "height": latest.get("height"),
        "uploader": oldest.get("user"),
        "uploaded_at": _parse_ts(oldest.get("timestamp")),
        "file_url": latest.get("url"),
    }


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

        # First revision ever: creator + creation date (Fountain's
        # submitterIsCreator / articleCreated rules need these).
        first = client.get(api_url(domain), params={
            "action": "query", "format": "json", "formatversion": 2,
            "prop": "revisions", "pageids": meta.page_id,
            "rvprop": "timestamp|user", "rvdir": "newer", "rvlimit": 1,
        }).json()
        first_pages = first.get("query", {}).get("pages", [])
        if first_pages and first_pages[0].get("revisions"):
            rev0 = first_pages[0]["revisions"][0]
            meta.creator = rev0.get("user")
            ts = rev0.get("timestamp")
            if ts:
                meta.created_at = datetime.strptime(
                    ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        meta.is_new_page = (
            meta.creator == username
            and meta.created_at is not None
            and _iso(start) <= meta.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            <= _iso(end, end=True)
        )

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

        prev_size = base_size
        added = 0
        for rev in revs:
            size = rev.get("size", prev_size)
            if rev.get("user") == username:
                added += max(0, size - prev_size)
            prev_size = size
        meta.bytes_added = added
    return meta

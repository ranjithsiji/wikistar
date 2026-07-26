"""Read-only MediaWiki / Wikidata API client (httpx, no auth needed).

Used to verify submissions instead of trusting user input:
  * does the page exist, its size and current revision
  * how many bytes the participant added during the campaign window
  * whether the participant created the page during the window
"""
import re
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
    # QID of the Wikidata item connected to this page (P: wikibase_item),
    # used to match articles against suggested items by sitelink.
    wikidata_qid: str | None = None


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


def fetch_wikibase_items(domain: str, titles: list[str]) -> dict[str, str]:
    """The connected Wikidata QID for each of the given page titles on
    `domain`, as {title: qid} (titles with no connected item are
    omitted). Batched: up to 50 titles per API call."""
    result: dict[str, str] = {}
    if not titles:
        return result
    with _client() as client:
        for start in range(0, len(titles), 50):  # API limit: 50 titles per call
            chunk = titles[start:start + 50]
            data = client.get(api_url(domain), params={
                "action": "query", "format": "json", "formatversion": 2,
                "prop": "pageprops", "ppprop": "wikibase_item",
                "titles": "|".join(chunk),
            }).json()
            for page in data.get("query", {}).get("pages", []):
                qid = (page.get("pageprops") or {}).get("wikibase_item")
                if qid:
                    result[page.get("title", "")] = qid
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


def _latest_revision(client: httpx.Client, domain: str, page_id: int) -> dict:
    data = client.get(api_url(domain), params={
        "action": "query", "format": "json", "formatversion": 2,
        "prop": "revisions", "pageids": page_id,
        "rvprop": "timestamp|user", "rvdir": "older", "rvlimit": 1,
    }).json()
    pages = data.get("query", {}).get("pages", [])
    if pages and pages[0].get("revisions"):
        return pages[0]["revisions"][0]
    return {}


def add_page_template(domain: str, title: str, template: str,
                      on_talk: bool, access_token: str) -> bool:
    """Prepend {{template}} to the article (or its talk page) with the
    user's own OAuth token. Returns True on success; never raises for
    API-level failures — callers treat the write as best-effort."""
    target = f"Talk:{title}" if on_talk else title
    wikitext = f"{{{{{template}}}}}\n"
    headers = {"User-Agent": USER_AGENT,
               "Authorization": f"Bearer {access_token}"}
    with httpx.Client(headers=headers, timeout=TIMEOUT) as client:
        data = client.get(api_url(domain), params={
            "action": "query", "format": "json", "meta": "tokens",
            "type": "csrf",
        }).json()
        csrf = data.get("query", {}).get("tokens", {}).get("csrftoken", "")
        if not csrf or csrf == "+\\":  # anonymous: the token was not accepted
            return False
        payload = {
            "action": "edit", "format": "json", "title": target,
            "prependtext": wikitext, "token": csrf,
            "summary": f"Adding {{{{{template}}}}} "
                       "([[wikitech:Tool:WikiSTAR|WikiSTAR]])",
        }
        if not on_talk:
            payload["nocreate"] = "1"  # never create the article itself
        result = client.post(api_url(domain), data=payload).json()
    return result.get("edit", {}).get("result") == "Success"


def fetch_user_contribs(domain: str, username: str, start: date, end: date,
                        namespace: int = 0,
                        limit: int | None = None) -> list[dict]:
    """A user's edits on the wiki inside [start, end], as
    {"title", "comment"} dicts. With `limit`, pagination stops as soon as
    more than `limit` edits are seen (the result then has limit+1 or more
    entries) — callers use that to bail out of huge tool-driven runs."""
    revs: list[dict] = []
    params = {
        "action": "query", "format": "json", "formatversion": 2,
        "list": "usercontribs", "ucuser": username,
        "ucnamespace": namespace, "ucprop": "title|comment",
        "uclimit": "max",
        # usercontribs walks newest -> oldest: start is the newer bound.
        "ucstart": _iso(end, end=True), "ucend": _iso(start),
    }
    with _client() as client:
        while True:
            data = client.get(api_url(domain), params=params).json()
            revs.extend(data.get("query", {}).get("usercontribs", []))
            cont = data.get("continue")
            if not cont or (limit is not None and len(revs) > limit):
                break
            params.update(cont)
    return revs


# Wikibase auto-summaries, e.g. "/* wbsetclaim-create:2||1 */ [[Property:P31]]…"
# Statements: creating/editing/removing a claim, its qualifiers, its
# references, or its rank — all real curation work on the item's facts.
# wbsetclaim-update-{rank,qualifiers,references} are distinct autocomment
# keys from plain wbsetclaim-update, so the base "wbsetclaim-update" match
# (a prefix of all three) covers them without listing each separately.
# wbcreateclaim also has legacy -value/-novalue/-somevalue variants.
_STATEMENT_RE = re.compile(
    r"^/\* wb("
    r"setclaim-(create|update)"
    r"|createclaim(-create|-value|-novalue|-somevalue)?"
    r"|setclaimvalue"
    r"|removeclaims?(-remove|-update)?"
    r"|set(qualifier|reference)(-add|-set)?"
    r"|remove(qualifiers|references)(-remove|-update)?"
    r")")
# Labels/descriptions/aliases (incl. removal), plus sitelinks
# (wbsetsitelink-*, wblinktitles-connect) — connecting a page to the item
# is the same kind of identity-enriching edit as adding a label.
_TERM_RE = re.compile(
    r"^/\* wb("
    r"set(label|description)-(add|set|remove)"
    r"|setaliases-(add|set|remove|add-remove|update)"
    r"|setsitelink-(add|add-both|set|set-badges|set-both|remove)"
    r"|linktitles-(connect|create)"
    r")")
# Commons structured data: "…EntityPage/P180]]: [[d:Special:EntityPage/Q42]]"
_DEPICTS_RE = re.compile(r"EntityPage/P180\]\]: \[\[d:Special:EntityPage/(Q\d+)")


def fetch_wikidata_user_activity(username: str, start: date, end: date,
                                 max_edits: int | None = None
                                 ) -> dict[str, dict] | None:
    """Per-item counts of the user's Wikidata work in the window:
    {qid: {"statements": n, "terms": n}} — statement creations and
    label/description/alias edits, classified from the auto-summaries.
    Returns None when the user made more than `max_edits` edits (too
    much to score automatically, e.g. a QuickStatements batch)."""
    revs = fetch_user_contribs("www.wikidata.org", username, start, end,
                               limit=max_edits)
    if max_edits is not None and len(revs) > max_edits:
        return None
    out: dict[str, dict] = {}
    for rev in revs:
        qid = rev.get("title", "")
        if not qid.startswith("Q"):
            continue
        comment = rev.get("comment", "")
        entry = out.setdefault(qid, {"statements": 0, "terms": 0})
        if _STATEMENT_RE.match(comment):
            entry["statements"] += 1
        elif _TERM_RE.match(comment):
            entry["terms"] += 1
    return {q: v for q, v in out.items() if v["statements"] or v["terms"]}


def fetch_eligible_qids(qids: list[str], any_of: list[str]) -> set[str]:
    """Items whose claims satisfy at least one "P17=Q668"-style
    constraint. An empty constraint list means everything is eligible."""
    if not any_of:
        return set(qids)
    pairs = [c.split("=", 1) for c in any_of if "=" in c]
    eligible: set[str] = set()
    with _client() as client:
        for i in range(0, len(qids), 50):  # API limit: 50 ids per call
            chunk = qids[i:i + 50]
            data = client.get(api_url("www.wikidata.org"), params={
                "action": "wbgetentities", "format": "json",
                "ids": "|".join(chunk), "props": "claims",
            }).json()
            for qid, entity in (data.get("entities") or {}).items():
                claims = entity.get("claims") or {}
                if any(
                    isinstance(v := (cl.get("mainsnak", {})
                                     .get("datavalue", {}).get("value")), dict)
                    and v.get("id") == target
                    for prop, target in pairs
                    for cl in claims.get(prop, [])
                ):
                    eligible.add(qid)
    return eligible


def fetch_commons_user_activity(username: str, start: date, end: date,
                                depicts_targets: list[str] | None = None,
                                max_edits: int | None = None
                                ) -> dict | None:
    """The user's Commons work in the window: new file uploads and
    depicts (P180) statements added, optionally restricted to the given
    target QIDs. Returns None when the uploads or file edits exceed
    `max_edits` (too much to score automatically)."""
    uploads = 0
    params = {
        "action": "query", "format": "json", "formatversion": 2,
        "list": "logevents", "letype": "upload", "leuser": username,
        "lelimit": "max", "lestart": _iso(end, end=True), "leend": _iso(start),
    }
    with _client() as client:
        while True:
            data = client.get(api_url("commons.wikimedia.org"),
                              params=params).json()
            uploads += sum(1 for ev in data.get("query", {})
                           .get("logevents", [])
                           if ev.get("action") == "upload")
            cont = data.get("continue")
            if max_edits is not None and uploads > max_edits:
                return None
            if not cont:
                break
            params.update(cont)

    revs = fetch_user_contribs("commons.wikimedia.org", username,
                               start, end, namespace=6, limit=max_edits)
    if max_edits is not None and len(revs) > max_edits:
        return None
    targets = {t.strip().upper() for t in depicts_targets or [] if t.strip()}
    depicts = 0
    for rev in revs:
        m = _DEPICTS_RE.search(rev.get("comment", ""))
        if m and (not targets or m.group(1) in targets):
            depicts += 1
    return {"uploads": uploads, "depicts": depicts}


def fetch_article_details(domain: str, title: str) -> dict | None:
    """Live per-article facts for the participant popup and submission card:
    size, word count, creation/last-edit dates and editors, the connected
    Wikidata item, and — for a non-English wiki — that item's English
    label/sitelink title, so a non-English submission can show its
    English name alongside the native title. Returns None for a missing
    page; network errors raise httpx.HTTPError."""
    lang = domain.split(".")[0]
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
        latest = _latest_revision(client, domain, page["pageid"])
        extract = client.get(api_url(domain), params={
            "action": "query", "format": "json", "formatversion": 2,
            "prop": "extracts", "explaintext": 1, "exlimit": 1,
            "titles": title,
        }).json()
        text = extract["query"]["pages"][0].get("extract") or ""
        qid = (page.get("pageprops") or {}).get("wikibase_item")
        label_en = title_en = None
        if qid and lang != "en":
            sitelinks = fetch_sitelinks([qid], ["en"]).get(qid) or {}
            label_en = sitelinks.get("label_en")
            title_en = sitelinks.get("links", {}).get("en")
    return {
        "bytes": page.get("length"),
        "words": len(text.split()),
        "created_at": _parse_ts(first.get("timestamp")),
        "created_by": first.get("user"),
        "last_updated": _parse_ts(page.get("touched")),
        "last_updated_by": latest.get("user"),
        "qid": qid,
        "label_en": label_en,
        "title_en": title_en,
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
        latest = _latest_revision(client, domain, page["pageid"])
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
        "created_by": first.get("user"),
        "last_updated": _parse_ts(page.get("touched")),
        "last_updated_by": latest.get("user"),
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


# Claims are capped in the preview popup: it's a quick glance, not a full
# item dump, and resolving every property label would be an unbounded
# number of extra API calls for items with dozens of statements.
MAX_PREVIEW_CLAIMS = 12


def fetch_article_preview(domain: str, title: str) -> dict | None:
    """Rendered HTML of the current revision, for the submission preview
    popup. Returns None for a missing page; network errors raise
    httpx.HTTPError. The lead section only (section 0) keeps the popup a
    quick glance rather than a full mirrored article."""
    with _client() as client:
        data = client.get(api_url(domain), params={
            "action": "parse", "format": "json", "formatversion": 2,
            "page": title, "prop": "text", "section": "0",
            "disabletoc": 1, "disableeditsection": 1,
        }).json()
    if "error" in data:
        return None
    parse = data.get("parse") or {}
    return {"title": parse.get("title", title), "html": parse.get("text", "")}


def fetch_wikidata_preview(qid: str) -> dict | None:
    """Label, description, aliases and a capped list of claims (property
    label -> formatted value strings) for the submission preview popup.
    Returns None if the item is missing."""
    with _client() as client:
        entity = client.get(api_url("www.wikidata.org"), params={
            "action": "wbgetentities", "format": "json", "ids": qid,
            "props": "labels|descriptions|aliases|claims",
            "languages": "en|mul",
        }).json().get("entities", {}).get(qid)
        if not entity or "missing" in entity:
            return None
        labels = entity.get("labels") or {}
        descriptions = entity.get("descriptions") or {}
        aliases = [a["value"] for a in (entity.get("aliases") or {}).get("en", [])]
        claims = entity.get("claims") or {}
        prop_ids = list(claims.keys())[:MAX_PREVIEW_CLAIMS]
        prop_labels: dict[str, str] = {}
        if prop_ids:
            data = client.get(api_url("www.wikidata.org"), params={
                "action": "wbgetentities", "format": "json",
                "ids": "|".join(prop_ids), "props": "labels",
                "languages": "en",
            }).json()
            for pid, pentity in (data.get("entities") or {}).items():
                lbl = (pentity.get("labels") or {}).get("en", {}).get("value")
                prop_labels[pid] = lbl or pid
        rows = []
        for pid in prop_ids:
            values = []
            for snak in claims[pid][:5]:
                dv = (snak.get("mainsnak", {}) or {}).get("datavalue", {}) or {}
                v = dv.get("value")
                if isinstance(v, dict):
                    text = v.get("id") or v.get("text") or v.get("time") or str(v)
                elif v is None:
                    text = "unknown value"
                else:
                    text = str(v)
                values.append(text)
            rows.append({"property": prop_labels.get(pid, pid), "values": values})
    return {
        "qid": qid.upper(),
        "label": (labels.get("en") or labels.get("mul") or {}).get("value"),
        "description": (descriptions.get("en") or descriptions.get("mul") or {}).get("value"),
        "aliases": aliases,
        "claims": rows,
        "claim_count": len(claims),
    }


def _bytes_added(revs: list[dict], base_size: int, username: str) -> int:
    """Sum (size_after - size_before) — positive AND negative — over the
    given user's own revisions (oldest -> newest), floored at 0.

    Other editors' revisions only advance the running "previous size"
    baseline; they're never credited or blamed. Summing signed deltas
    (not just the positive ones) means a user's own trim-then-re-add
    churn nets out instead of the same bytes being counted as growth
    every time they're re-added.
    """
    prev_size = base_size
    added = 0
    for rev in revs:
        size = rev.get("size", prev_size)
        if rev.get("user") == username:
            added += size - prev_size
        prev_size = size
    return max(0, added)


def fetch_page_metadata(
    domain: str, title: str, username: str, start: date, end: date
) -> PageMetadata:
    """Fetch page info and the participant's byte delta within [start, end]
    (see _bytes_added for exactly how bytes_added is computed). Network
    errors raise httpx.HTTPError — callers decide whether that is fatal
    (submission still accepted, metadata refreshable later).
    """
    meta = PageMetadata()
    with _client() as client:
        info = client.get(api_url(domain), params={
            "action": "query", "format": "json", "formatversion": 2,
            "prop": "info|pageprops", "ppprop": "wikibase_item",
            "titles": title,
        }).json()
        page = info["query"]["pages"][0]
        if page.get("missing"):
            return meta
        meta.exists = True
        meta.page_id = page["pageid"]
        meta.page_len = page.get("length")
        meta.current_rev_id = page.get("lastrevid")
        meta.wikidata_qid = (page.get("pageprops") or {}).get("wikibase_item")

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

        meta.bytes_added = _bytes_added(revs, base_size, username)
    return meta

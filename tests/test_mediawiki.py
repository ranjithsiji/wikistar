"""Pure-function tests for integrations/mediawiki.py's revision-delta math."""
from datetime import date

import integrations.mediawiki as mediawiki
from integrations.mediawiki import _bytes_added, fetch_wikidata_user_activity


def test_clean_creation_sums_to_final_size():
    # Erissery: created from scratch, every revision by the same user,
    # sizes only ever go up (mod one no-op save) -> signed sum == gross sum.
    revs = [
        {"user": "A", "size": 1586}, {"user": "A", "size": 2773},
        {"user": "A", "size": 3476}, {"user": "A", "size": 3785},
        {"user": "A", "size": 3785}, {"user": "A", "size": 3829},
        {"user": "A", "size": 4066}, {"user": "A", "size": 4302},
        {"user": "A", "size": 4818}, {"user": "A", "size": 5002},
        {"user": "A", "size": 5461}, {"user": "A", "size": 6454},
        {"user": "A", "size": 6552}, {"user": "A", "size": 6549},
        {"user": "A", "size": 6550},
    ]
    assert _bytes_added(revs, base_size=0, username="A") == 6550


def test_own_negative_deltas_are_netted_not_discarded():
    # A user who adds 1000 bytes then trims 400 of their own prose nets
    # 600 -- the old buggy behavior (max(0, delta) per revision) would
    # have counted 1000 and ignored the trim entirely.
    revs = [{"user": "A", "size": 1000}, {"user": "A", "size": 600}]
    assert _bytes_added(revs, base_size=0, username="A") == 600


def test_other_editors_move_the_baseline_but_are_not_credited():
    # Bearcat's -129 edit is real content, not A's -- it must shift the
    # baseline for A's next delta without being added to A's total.
    revs = [
        {"user": "A", "size": 1000},
        {"user": "Bearcat", "size": 871},   # -129, not A's
        {"user": "A", "size": 921},          # +50 off the new baseline
    ]
    assert _bytes_added(revs, base_size=0, username="A") == 1050


def test_net_negative_floors_at_zero():
    # A user who trims more than they add nets negative over the window;
    # bytes_added is never negative.
    revs = [{"user": "A", "size": 1000}, {"user": "A", "size": 200}]
    assert _bytes_added(revs, base_size=1000, username="A") == 0


def test_same_user_follows_mediawiki_name_normalisation():
    # MediaWiki reads underscores as spaces and capitalises the first
    # letter, so these all name one account. The wiki answers with its own
    # spelling while the stored name comes from the OAuth profile, so a
    # verbatim comparison could call a page's own creator a stranger.
    assert mediawiki.same_user("Meenakshi nandhini", "Meenakshi_nandhini")
    assert mediawiki.same_user("meenakshi nandhini", "Meenakshi nandhini")
    assert mediawiki.same_user("Ranjith  siji", "Ranjith siji")
    # Genuinely different people must never collapse together.
    assert not mediawiki.same_user("Meenakshi", "Meenakshi nandhini")
    assert not mediawiki.same_user("Alice", "Bob")
    # Only the FIRST letter is case-insensitive; the rest is significant.
    assert not mediawiki.same_user("Meenakshi Nandhini", "Meenakshi nandhini")
    # A missing creator (deleted revision) is nobody, not a match.
    assert not mediawiki.same_user(None, "Alice")
    assert not mediawiki.same_user("", "")


def test_page_metadata_follows_a_redirect_left_by_a_rename(monkeypatch):
    """A page renamed after submission leaves the submitted title behind
    as a redirect. Reading the redirect stub instead of the article makes
    the submitter's own work look like 0 bytes by someone else, and a
    recalculation would then strip their points."""
    calls = []

    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

    class FakeClient:
        def get(self, url, params=None):
            calls.append(params)
            # The info query: only answered with the article when the
            # caller asked the wiki to resolve redirects.
            if params.get("prop", "").startswith("info"):
                if not params.get("redirects"):
                    # the stub: tiny, created by whoever moved the page
                    return FakeResponse({"query": {"pages": [
                        {"pageid": 999, "length": 91, "lastrevid": 5}]}})
                return FakeResponse({"query": {"pages": [
                    {"pageid": 123, "length": 11717, "lastrevid": 4652368}]}})
            if params.get("rvdir") == "newer" and params.get("rvlimit") == 1:
                return FakeResponse({"query": {"pages": [{"revisions": [
                    {"timestamp": "2026-07-20T10:00:00Z",
                     "user": "Atheenasiji"}]}]}})
            if params.get("rvlimit") == "max":
                return FakeResponse({"query": {"pages": [{"revisions": [
                    {"size": 11717, "user": "Atheenasiji", "parentid": 0,
                     "timestamp": "2026-07-20T10:00:00Z"}]}]}})
            return FakeResponse({"query": {"pages": []}})

    from contextlib import contextmanager

    @contextmanager
    def fake_client():
        yield FakeClient()

    monkeypatch.setattr(mediawiki, "_client", fake_client)
    meta = mediawiki.fetch_page_metadata(
        "ml.wikipedia.org", "Old title", "Atheenasiji",
        date(2026, 7, 15), date(2026, 8, 15))

    assert calls[0].get("redirects"), "the info query must resolve redirects"
    assert meta.page_len == 11717      # the article, not the 91-byte stub
    assert meta.is_new_page is True
    assert meta.bytes_added == 11717


def test_bytes_are_credited_across_username_spellings():
    # The revision history spells the user one way and the stored account
    # another; the edits are still theirs.
    revs = [{"user": "Meenakshi nandhini", "size": 4000}]
    assert _bytes_added(revs, base_size=0,
                        username="Meenakshi_nandhini") == 4000


def test_feminism_in_kerala_matches_the_real_edit_history():
    # Real revision history of https://en.wikipedia.org/wiki/Feminism_in_Kerala
    # (oldest -> newest, from the MediaWiki API): Netha Hussain created the
    # article and made many small edits, some positive and some negative,
    # ending at 18,293 bytes; Bearcat made one unrelated -129 edit partway
    # through. Summing every SIGNED delta of Netha's own revisions (not
    # just the positive ones, and not Bearcat's) gives 18,422 ->
    # floor(18,422 / 1000) = 18 points, not the 19 the old
    # gross-positive-sum bug produced.
    users = ["Netha Hussain"] * 25 + ["Bearcat"] + ["Netha Hussain"] * 13
    sizes = [17899, 17899, 17903, 17922, 17926, 17911, 17919, 17915, 17933,
             17913, 17840, 17844, 17848, 17915, 17914, 17883, 17883, 17869,
             17865, 17822, 17792, 17575, 17596, 17962, 18165, 18036, 18215,
             18260, 18344, 18355, 18361, 18361, 18348, 18348, 18191, 18192,
             18224, 18255, 18293]
    assert len(users) == len(sizes) == 39
    revs = [{"user": u, "size": s} for u, s in zip(users, sizes)]
    assert _bytes_added(revs, base_size=0, username="Netha Hussain") == 18422


def test_chundan_vallam_matches_the_real_edit_history():
    # https://en.wikipedia.org/wiki/Chundan_vallam - Netha Hussain's edits
    # (all on 2026-07-22) monotonically grow the article with no
    # self-reversion, so the signed sum equals net growth: 7,033 (final)
    # - 3,578 (size before her first edit) = 3,455 -> 3 points.
    sizes = [5022, 5324, 5843, 6094, 6095, 6072, 6072, 7033]
    revs = [{"user": "Netha Hussain", "size": s} for s in sizes]
    assert _bytes_added(revs, base_size=3578, username="Netha Hussain") == 3455


def test_kappa_varutthathu_matches_the_real_edit_history():
    # https://ml.wikipedia.org/wiki/കപ്പ_വറുത്തത് - SijiR created the
    # article (base 0) and made almost all the edits; Ranjithsiji and
    # Malikaveedu each made a couple of interleaved edits that shift the
    # baseline but aren't credited/blamed to SijiR.
    users = ['SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'Ranjithsiji', 'Ranjithsiji', 'SijiR', 'SijiR', 'SijiR', 'SijiR',
             'SijiR', 'Ranjithsiji', 'Malikaveedu']
    sizes = [401, 1253, 2075, 2886, 3348, 3393, 3464, 3693, 3939, 5824, 5865,
             5930, 5974, 6178, 7690, 9155, 9250, 11746, 11782, 11825, 11864,
             11907, 11962, 12234, 12283, 12495, 12516, 12538, 12558, 12558,
             12655, 12659, 12664, 12668, 12674, 12694, 12088, 12097, 12094,
             12118, 12177, 12181, 12149, 12092, 12028, 11634, 11631, 11555,
             11595, 11613, 11689]
    assert len(users) == len(sizes) == 51
    revs = [{"user": u, "size": s} for u, s in zip(users, sizes)]
    assert _bytes_added(revs, base_size=0, username="SijiR") == 11684


def test_wikidata_sitelink_connect_counts_as_a_term_edit(monkeypatch):
    # https://www.wikidata.org/wiki/Q21063857 - Ranjithsiji made 5 real
    # edits: 2 descriptions, 1 label, 1 statement, and 1 sitelink connect
    # (wblinktitles-connect, from merging enwiki/mlwiki sitelinks in).
    # The sitelink connect wasn't recognised by the classifier, so the
    # combined count landed on 4 and missed the suggested-list bonus's
    # 5-edit gate by one - it must count as a term edit like labels do.
    comments = [
        "/* wbsetdescription-add:1|hi */ x",
        "/* wbsetlabel-add:1|hi */ x",
        "/* wbsetclaim-create:2||1 */ x",
        "/* wbsetdescription-add:1|ml */ x",
        "/* wblinktitles-connect:2| */ enwiki:Jayaraj Vijay, mlwiki:x",
    ]
    revs = [{"title": "Q21063857", "comment": c} for c in comments]
    monkeypatch.setattr(mediawiki, "fetch_user_contribs", lambda *a, **k: revs)
    activity = fetch_wikidata_user_activity(
        "Ranjithsiji", date(2026, 7, 15), date(2026, 8, 15))
    assert activity["Q21063857"] == {"statements": 1, "terms": 4}


def test_wikidata_claim_update_counts_as_a_statement_edit(monkeypatch):
    # https://www.wikidata.org/wiki/Q1426089 - பொதுஉதவி made 5 real edits:
    # 2 claim creates, 1 claim update (correcting the coordinate value),
    # and 2 description changes. wbsetclaim-update wasn't recognised by
    # the classifier (only wbsetclaim-create was), so the combined count
    # landed on 4 and missed the suggested-list bonus's 5-edit gate by
    # one - editing an existing statement is a real contribution too.
    comments = [
        "/* wbsetclaim-create:2||1 */ x",
        "/* wbsetclaim-create:2||1 */ x",
        "/* wbsetclaim-update:2||1 */ x",
        "/* wbsetdescription-set:1|ta */ x",
        "/* wbsetdescription-set:1|en */ x",
    ]
    revs = [{"title": "Q1426089", "comment": c} for c in comments]
    monkeypatch.setattr(mediawiki, "fetch_user_contribs", lambda *a, **k: revs)
    activity = fetch_wikidata_user_activity(
        "பொதுஉதவி", date(2026, 7, 15), date(2026, 8, 15))
    assert activity["Q1426089"] == {"statements": 3, "terms": 2}


def test_qualifier_reference_rank_and_remove_edits_all_count(monkeypatch):
    # Full audit of Wikibase autocomment keys (wikimedia/Wikibase i18n)
    # turned up several more real-edit verbs that weren't recognised by
    # either classifier: rank changes, qualifier/reference add/remove
    # (both the dedicated API and the generic setclaim path), claim
    # removal, and the "remove" variant of label/description/alias/
    # sitelink edits. All represent real curation work and must count.
    statement_comments = [
        "/* wbsetclaim-update-rank:2||1 */ x",
        "/* wbsetclaim-update-qualifiers:2||1 */ x",
        "/* wbsetclaim-update-references:2||1 */ x",
        "/* wbsetqualifier-add:1| */ x",
        "/* wbremovequalifiers-remove:1| */ x",
        "/* wbsetreference-add:2| */ x",
        "/* wbremovereferences-remove:1| */ x",
        "/* wbremoveclaims-remove:1| */ x",
    ]
    term_comments = [
        "/* wbsetlabel-remove:1|en */ x",
        "/* wbsetdescription-remove:1|en */ x",
        "/* wbsetaliases-remove:1|en */ x",
        "/* wbsetsitelink-remove:1|enwiki */ x",
    ]
    revs = [{"title": "Q1", "comment": c} for c in statement_comments + term_comments]
    monkeypatch.setattr(mediawiki, "fetch_user_contribs", lambda *a, **k: revs)
    activity = fetch_wikidata_user_activity(
        "Tester", date(2026, 7, 15), date(2026, 8, 15))
    assert activity["Q1"] == {
        "statements": len(statement_comments), "terms": len(term_comments)}


def test_undo_restore_and_merge_are_not_counted(monkeypatch):
    # Reverts and item merges aren't the acting user contributing new
    # content — they must stay uncounted, not silently miscounted as
    # either bucket.
    comments = [
        "/* wbsetclaim-create:2||1 */ x (restore)",
        "undo",
        "/* wbmergeitems-from:0| */ x",
        "/* wbmergeitems-to:0| */ x",
        "/* wbcreateredirect:0| */ x",
    ]
    revs = [{"title": "Q2", "comment": c} for c in comments]
    monkeypatch.setattr(mediawiki, "fetch_user_contribs", lambda *a, **k: revs)
    activity = fetch_wikidata_user_activity(
        "Tester", date(2026, 7, 15), date(2026, 8, 15))
    # only the first comment (a real wbsetclaim-create, "(restore)" is
    # just an incidental suffix MediaWiki appends) should count
    assert activity["Q2"] == {"statements": 1, "terms": 0}


def test_wikibase_items_keyed_by_the_title_asked_for(monkeypatch):
    # The API rewrites titles on the way in: "united_states" is
    # normalised to "United states", "USA" is a redirect to "United
    # States", and several inputs can collapse onto one page. Keying the
    # result by the title the wiki *returns* would leave callers unable
    # to look up the title they passed -- which silently broke matching a
    # suggested article (pasted from a URL, so underscored) against the
    # submission for the same page.
    payload = {"query": {
        "normalized": [
            {"from": "United_States", "to": "United States"},
            {"from": "usa", "to": "Usa"},
        ],
        "redirects": [{"from": "Usa", "to": "United States"}],
        "pages": [
            {"title": "United States", "pageprops": {"wikibase_item": "Q30"}},
            {"title": "Nowhere", "missing": True},
        ],
    }}

    class FakeResponse:
        def json(self):
            return payload

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, *a, **k):
            return FakeResponse()

    monkeypatch.setattr(mediawiki, "_client", FakeClient)
    result = mediawiki.fetch_wikibase_items(
        "en.wikipedia.org", ["United_States", "usa", "United States", "Nowhere"])

    # every spelling that leads to the page resolves, including the
    # two-hop one (normalise "usa" -> "Usa", then redirect -> "United States")
    assert result["United_States"] == "Q30"
    assert result["usa"] == "Q30"
    assert result["United States"] == "Q30"
    assert "Nowhere" not in result


def test_fetch_item_user_edits_classifies_and_filters(monkeypatch):
    # One item's history filtered by user (rvuser): statement edits and
    # term edits are classified by auto-summary, anything else ignored.
    seen_params = {}
    payload = {"query": {"pages": [{"title": "Q500", "revisions": [
        {"comment": "/* wbsetclaim-create:2||1 */ [[Property:P31]]: [[Q5]]"},
        {"comment": "/* wbsetlabel-add:1|ml */ label"},
        {"comment": "/* wbsetdescription-set:1|en */ desc"},
        {"comment": "reverted vandalism"},  # manual edit: neither bucket
    ]}]}}

    class FakeResponse:
        def json(self):
            return payload

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url, params=None, **k):
            seen_params.update(params or {})
            return FakeResponse()

    monkeypatch.setattr(mediawiki, "_client", FakeClient)
    counts = mediawiki.fetch_item_user_edits(
        "Q500", "Dana", date(2026, 1, 1), date(2026, 1, 31))

    assert counts == {"statements": 1, "terms": 2}
    # the request asks the item's own history for just this user's edits
    assert seen_params["titles"] == "Q500"
    assert seen_params["rvuser"] == "Dana"

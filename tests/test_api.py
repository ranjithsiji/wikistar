"""End-to-end API tests over the real app with a MariaDB test database.

Auth uses the real signed session cookie (set via the test client's
session_transaction); MediaWiki lookups are monkeypatched.
"""
from datetime import date, timedelta

import pytest

import mediawiki
from app import app
from db import Base, SessionLocal, engine
from mediawiki import PageMetadata
from models import User

TODAY = date.today()

_client = None


@pytest.fixture(scope="module")
def client():
    global _client
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.config["TESTING"] = True
    with app.test_client() as c:
        _client = c
        yield c
    _client = None


SYSOP_WIKIS: dict[str, set] = {}


@pytest.fixture(autouse=True)
def fake_mediawiki(monkeypatch):
    monkeypatch.setattr(mediawiki, "fetch_sysop_wikis",
                        lambda username: SYSOP_WIKIS.get(username, set()))

    def fake_fetch(domain, title, username, start, end):
        if title == "Kathakali":
            return PageMetadata(exists=True, page_id=11, page_len=20000,
                                current_rev_id=2, base_rev_id=1,
                                bytes_added=5000, is_new_page=False)
        if title == "Stub":
            return PageMetadata(exists=True, page_id=13, page_len=300,
                                current_rev_id=5, base_rev_id=4,
                                bytes_added=120, is_new_page=False)
        return PageMetadata(exists=True, page_id=12, page_len=4100,
                            current_rev_id=4, base_rev_id=None,
                            bytes_added=4100, is_new_page=True)
    monkeypatch.setattr(mediawiki, "fetch_page_metadata", fake_fetch)


def login(username: str, is_admin: bool = False) -> int:
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(username=username).first()
        if user is None:
            user = User(username=username)
            db.add(user)
        user.is_admin = is_admin
        db.commit()
        user_id = user.id
    finally:
        db.close()
    with _client.session_transaction() as s:
        s["user_id"] = user_id
    return user_id


def logout():
    with _client.session_transaction() as s:
        s.pop("user_id", None)


def make_campaign_payload(client, mode="self", **extra):
    meta = client.get("/api/meta").json
    payload = {
        "name": "Kerala Culture Contest",
        "description": "Improve Kerala culture coverage",
        "language": "ml",
        "start_date": (TODAY - timedelta(days=5)).isoformat(),
        "end_date": (TODAY + timedelta(days=25)).isoformat(),
        "scoring_mode": mode,
        "settings": {"allow_wikidata_items": True},
        "rules": meta["default_rules"]["self"],
        "jury_usernames": ["JuryBob"],
        "suggested_articles": ["Kathakali", "Theyyam"],
        "suggested_items": ["Q126"],
    }
    payload.update(extra)
    return payload


def test_full_self_assessment_flow(client):
    # --- create (organizer) -------------------------------------------------
    logout()
    r = client.post("/api/campaigns", json=make_campaign_payload(client))
    assert r.status_code == 401

    login("Alice")
    r = client.post("/api/campaigns", json=make_campaign_payload(client))
    assert r.status_code == 201, r.text
    camp = r.json
    slug = camp["slug"]
    assert camp["status"] == "draft"
    assert "organizer" in camp["my_roles"]
    assert camp["settings"]["allow_wikidata_items"] is True
    assert camp["settings"]["show_leaderboard"] is True  # default merged in
    assert len(camp["rules"]) == 13

    # Draft hidden from strangers, visible to organizer
    logout()
    assert slug not in [c["slug"] for c in client.get("/api/campaigns").json]
    assert client.get(f"/api/campaigns/{slug}").status_code == 404
    login("Alice")
    assert slug in [c["slug"] for c in client.get("/api/campaigns").json]

    # --- approval (admin only) ----------------------------------------------
    login("Carol")
    assert client.post(f"/api/campaigns/{slug}/approve").status_code == 403
    login("Root", is_admin=True)
    r = client.post(f"/api/campaigns/{slug}/approve")
    assert r.status_code == 200 and r.json["status"] == "active"

    # --- participation ------------------------------------------------------
    login("Carol")
    r = client.post(f"/api/campaigns/{slug}/join")
    assert r.status_code == 200
    assert "participant" in r.json["my_roles"]

    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"title": "Kathakali", "kind": "article"})
    assert r.status_code == 201, r.text
    sub = r.json
    assert sub["bytes_added"] == 5000
    # 5 pts bytes (nearest) + 10 pts suggested list
    assert sub["points"] == 15

    # duplicate blocked
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"title": "Kathakali", "kind": "article"})
    assert r.status_code == 409

    # jury member blocked from submitting (jury_can_submit off)
    login("JuryBob")
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"title": "Theyyam", "kind": "article"})
    assert r.status_code == 403

    # --- claims ---------------------------------------------------------
    login("Carol")
    detail = client.get(f"/api/campaigns/{slug}").json
    improvement = next(r for r in detail["rules"]
                       if r["label"] == "Substantial improvement")
    ga = next(r for r in detail["rules"] if r["label"] == "Good Article")
    bytes_rule = next(r for r in detail["rules"]
                      if r["label"] == "Content added")

    r = client.put(f"/api/submissions/{sub['id']}/claims",
                   json=[{"rule_id": improvement["id"], "quantity": 1}])
    assert r.status_code == 200
    assert r.json["points"] == 17  # 5 + 10 + 2

    # auto rules are not claimable
    r = client.put(f"/api/submissions/{sub['id']}/claims",
                   json=[{"rule_id": bytes_rule["id"], "quantity": 99}])
    assert r.status_code == 400

    # someone else cannot claim on Carol's submission
    login("Alice")
    r = client.put(f"/api/submissions/{sub['id']}/claims",
                   json=[{"rule_id": ga["id"], "quantity": 1}])
    assert r.status_code == 403

    # --- moderation -----------------------------------------------------
    submissions = client.get(f"/api/campaigns/{slug}/submissions").json
    claim_id = submissions[0]["claims"][0]["id"]
    r = client.post(f"/api/claims/{claim_id}/moderate",
                    json={"status": "adjusted", "points_final": 1})
    assert r.status_code == 200
    submissions = client.get(f"/api/campaigns/{slug}/submissions").json
    assert submissions[0]["points"] == 16  # 5 + 10 + adjusted 1

    r = client.post(f"/api/submissions/{sub['id']}/moderate",
                    json={"points_override": 3})
    assert r.status_code == 200 and r.json["points"] == 3
    r = client.post(f"/api/submissions/{sub['id']}/moderate",
                    json={"clear_override": True})
    assert r.json["points"] == 16

    # --- leaderboard & stats ---------------------------------------------
    logout()
    board = client.get(f"/api/campaigns/{slug}/leaderboard").json
    assert board[0]["user"]["username"] == "Carol"
    assert board[0]["points"] == 16

    stats = client.get(f"/api/campaigns/{slug}/stats").json
    assert stats["submissions"] == 1
    assert stats["participants"] == 1
    assert stats["total_points"] == 16
    assert stats["by_kind"] == {"article": 1}
    assert stats["top_contributors"][0]["user"]["username"] == "Carol"
    assert len(stats["timeline"]) == 1


def test_jury_mode_flow(client):
    login("Alice")
    r = client.post("/api/campaigns", json=make_campaign_payload(
        client, mode="jury", name="Jury Contest", rules=[],
        settings={"jury_criteria": [
            {"key": "quality", "title": "Quality", "type": "int"}]}))
    assert r.status_code == 201, r.text
    slug = r.json["slug"]
    login("Root", is_admin=True)
    client.post(f"/api/campaigns/{slug}/approve")

    login("Dave")
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"title": "Onam", "kind": "article"})
    assert r.status_code == 201
    sub = r.json
    assert sub["points"] == 0  # no reviews yet

    # non-jury cannot review
    login("Carol")
    r = client.put(f"/api/submissions/{sub['id']}/review",
                   json={"total": 8, "decision": "accept"})
    assert r.status_code == 403

    # juror reviews
    login("JuryBob")
    # total is computed server-side from the marks config, not trusted
    r = client.put(f"/api/submissions/{sub['id']}/review",
                   json={"total": 999, "decision": "accept",
                         "scores": {"quality": 8}, "comment": "solid"})
    assert r.status_code == 200
    assert r.json["total"] == 8
    subs = client.get(f"/api/campaigns/{slug}/submissions").json
    assert subs[0]["points"] == 8

    # upsert: revising replaces, not duplicates
    r = client.put(f"/api/submissions/{sub['id']}/review",
                   json={"total": 6, "decision": "accept"})
    assert r.status_code == 200
    subs = client.get(f"/api/campaigns/{slug}/submissions").json
    assert subs[0]["points"] == 6
    assert len(subs[0]["reviews"]) == 1

    # claims are rejected in jury mode
    login("Dave")
    r = client.put(f"/api/submissions/{sub['id']}/claims", json=[])
    assert r.status_code == 400


def test_wiki_admin_approval_rules(client):
    """Fountain model: jury mode needs a sysop on the target wiki;
    self-assessment needs a sysop on any Wikipedia project."""
    SYSOP_WIKIS.clear()
    SYSOP_WIKIS["MlAdmin"] = {"ml.wikipedia.org"}
    SYSOP_WIKIS["CommonsAdmin"] = {"commons.wikimedia.org"}

    # jury campaign on ml.wikipedia.org created by its sysop -> auto-active
    login("MlAdmin")
    r = client.post("/api/campaigns", json=make_campaign_payload(
        client, mode="jury", name="ML Jury Contest", rules=[], language="ml"))
    assert r.status_code == 201 and r.json["status"] == "active"

    # ordinary creator stays draft; ml sysop can approve a jury campaign
    login("Alice")
    r = client.post("/api/campaigns", json=make_campaign_payload(
        client, mode="jury", name="ML Jury Draft", rules=[], language="ml"))
    slug = r.json["slug"]
    assert r.json["status"] == "draft"
    login("CommonsAdmin")  # sysop, but not on a Wikipedia -> no jury rights
    rights = client.get(f"/api/campaigns/{slug}/approval-rights").json
    assert rights["can_approve"] is False
    assert client.post(f"/api/campaigns/{slug}/approve").status_code == 403
    login("MlAdmin")
    assert client.post(f"/api/campaigns/{slug}/approve").status_code == 200

    # self-assessment: any Wikipedia sysop may approve, Commons may not
    login("Alice")
    r = client.post("/api/campaigns", json=make_campaign_payload(
        client, mode="self", name="Self Draft", language="ta"))
    slug = r.json["slug"]
    assert r.json["status"] == "draft"
    login("CommonsAdmin")
    assert client.post(f"/api/campaigns/{slug}/approve").status_code == 403
    login("MlAdmin")  # sysop on ml.wikipedia.org (not the target wiki) is fine
    r = client.post(f"/api/campaigns/{slug}/approve")
    assert r.status_code == 200 and r.json["status"] == "active"

    # a self campaign created by a Wikipedia sysop goes live immediately
    login("MlAdmin")
    r = client.post("/api/campaigns", json=make_campaign_payload(
        client, mode="self", name="Self by sysop", language="ta"))
    assert r.json["status"] == "active"
    SYSOP_WIKIS.clear()


def test_settings_validation_and_admin(client):
    login("Alice")
    bad = make_campaign_payload(client, name="Bad settings",
                                settings={"nonsense": True})
    assert client.post("/api/campaigns", json=bad).status_code == 400
    bad = make_campaign_payload(client, name="Bad type",
                                settings={"jury_can_submit": "yes"})
    assert client.post("/api/campaigns", json=bad).status_code == 400

    # admin endpoints gated and functional
    assert client.get("/api/admin/stats").status_code == 403
    login("Root", is_admin=True)
    stats = client.get("/api/admin/stats").json
    assert stats["campaigns"] >= 2 and stats["users"] >= 4
    logs = client.get("/api/admin/logs").json
    assert logs["total"] > 0
    users = client.get("/api/admin/users").json
    assert any(u["username"] == "Carol" for u in users)


def test_personal_dashboard(client):
    logout()
    assert client.get("/api/me/participation").status_code == 401

    # Carol submitted to the self-assessment campaign (first test)
    login("Carol")
    part = client.get("/api/me/participation").json
    assert len(part) >= 1
    rows = part[0]["rows"]
    me_rows = [r for r in rows if r["me"]]
    assert len(me_rows) == 1 and me_rows[0]["username"] == "Carol"
    assert me_rows[0]["points"] > 0

    # JuryBob is on the jury of both campaigns; the jury-mode one has
    # Dave's submission which JuryBob already reviewed -> missing == 0,
    # while Carol's self campaign submission is unreviewed -> missing == 1
    login("JuryBob")
    ev = client.get("/api/me/evaluation").json
    assert len(ev) >= 2
    assert {c["missing"] for c in ev} >= {0, 1}

    # Alice created the campaigns
    login("Alice")
    created = client.get("/api/me/created").json
    assert any(c["name"] == "Kerala Culture Contest" for c in created)

    # Approval: drafts visible to a site admin, none for a plain user
    assert client.get("/api/me/approval").json == []
    login("Root", is_admin=True)
    approvals = client.get("/api/me/approval").json
    assert all(c["status"] == "draft" for c in approvals)


def test_preferences_and_suggested_links(client, monkeypatch):
    logout()
    assert client.get("/api/me/preferences").status_code == 401

    login("Carol")
    assert client.get("/api/me/preferences").json == {
        "preferred_languages": [], "home_wikis": []}
    r = client.put("/api/me/preferences",
                   json={"preferred_languages": ["ML", " ta ", "en", "ml"],
                         "home_wikis": ["ML", "ta", "ml"]})
    assert r.status_code == 200
    assert r.json == {"preferred_languages": ["ml", "ta", "en"],
                      "home_wikis": ["ml", "ta"]}
    assert client.get("/api/me/preferences").json["home_wikis"] == ["ml", "ta"]
    assert client.put("/api/me/preferences",
                      json={"preferred_languages": ["bad code!"]}
                      ).status_code == 400
    assert client.put("/api/me/preferences",
                      json={"preferred_languages": ["ml", "ta", "en"],
                            "home_wikis": ["bad code!"]}).status_code == 400

    # suggested links resolve QIDs through Wikidata sitelinks in the
    # user's preferred languages
    def fake_sitelinks(qids, languages):
        assert qids == ["Q126"]
        return {"Q126": {"label": "Kerala", "label_en": "Kerala",
                         "links": {lang: f"Kerala ({lang})"
                                   for lang in languages if lang != "ta"}}}
    monkeypatch.setattr(mediawiki, "fetch_sitelinks", fake_sitelinks)

    slug = client.get("/api/campaigns").json[0]["slug"]
    data = client.get(f"/api/campaigns/{slug}/suggested-links").json
    assert data["languages"] == ["ml", "ta", "en"]
    item = data["items"][0]
    assert item["qid"] == "Q126" and item["label"] == "Kerala"
    assert item["label_en"] == "Kerala"
    assert [l["lang"] for l in item["links"]] == ["ml", "en"]
    assert item["links"][0]["url"] == "https://ml.wikipedia.org/wiki/Kerala_(ml)"

    # explicit ?languages= wins over the stored preference; English always
    # rides along for the suggested-items table
    data = client.get(
        f"/api/campaigns/{slug}/suggested-links?languages=en").json
    assert data["languages"] == ["en"]
    data = client.get(
        f"/api/campaigns/{slug}/suggested-links?languages=hi").json
    assert data["languages"] == ["hi", "en"]


def test_multi_language_submissions(client):
    login("Alice")
    r = client.post("/api/campaigns", json=make_campaign_payload(
        client, name="Multi Language Contest",
        settings={"multi_language": True}))
    assert r.status_code == 201, r.text
    slug = r.json["slug"]
    login("Root", is_admin=True)
    client.post(f"/api/campaigns/{slug}/approve")

    # participants pick the wiki per submission
    login("Eve")
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"title": "Onam", "kind": "article", "language": "ta"})
    assert r.status_code == 201, r.text
    assert r.json["wiki_domain"] == "ta.wikipedia.org"

    # the same title on another wiki is a separate submission
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"title": "Onam", "kind": "article", "language": "hi"})
    assert r.status_code == 201
    assert r.json["wiki_domain"] == "hi.wikipedia.org"

    # duplicate on the same wiki is still blocked
    assert client.post(
        f"/api/campaigns/{slug}/submissions",
        json={"title": "Onam", "kind": "article", "language": "ta"}
    ).status_code == 409

    # a single-language campaign ignores the language field
    login("Alice")
    r = client.post("/api/campaigns", json=make_campaign_payload(
        client, name="Single Language Contest"))
    slug2 = r.json["slug"]
    login("Root", is_admin=True)
    client.post(f"/api/campaigns/{slug2}/approve")
    login("Eve")
    r = client.post(f"/api/campaigns/{slug2}/submissions",
                    json={"title": "Onam", "kind": "article", "language": "ta"})
    assert r.status_code == 201
    assert r.json["wiki_domain"] == "ml.wikipedia.org"


def test_min_bytes_and_commons_depicts(client):
    login("Alice")
    r = client.post("/api/campaigns", json=make_campaign_payload(
        client, name="Commons Depicts Contest",
        settings={"allow_commons_files": True}))
    assert r.status_code == 201, r.text
    slug = r.json["slug"]
    login("Root", is_admin=True)
    client.post(f"/api/campaigns/{slug}/approve")

    detail = client.get(f"/api/campaigns/{slug}").json
    depicts = next(r for r in detail["rules"] if r["label"] == "Depicts added")
    improvement = next(r for r in detail["rules"]
                       if r["label"] == "Substantial improvement")
    assert improvement["params"] == {"min_bytes": 500}

    # Commons file submission earns depicts points per unit
    login("Frank")
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"title": "File:Kathakali dancer.jpg",
                          "kind": "commons_file"})
    assert r.status_code == 201, r.text
    sub = r.json
    assert sub["wiki_domain"] == "commons.wikimedia.org"
    r = client.put(f"/api/submissions/{sub['id']}/claims",
                   json=[{"rule_id": depicts["id"], "quantity": 3}])
    assert r.status_code == 200
    assert any(line["label"] == "Depicts added" and line["points"] == 3
               for line in r.json["breakdown"])

    # substantial improvement needs at least 500 added bytes
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"title": "Stub", "kind": "article"})
    assert r.status_code == 201
    stub = r.json
    assert stub["bytes_added"] == 120
    r = client.put(f"/api/submissions/{stub['id']}/claims",
                   json=[{"rule_id": improvement["id"], "quantity": 1}])
    assert r.status_code == 400
    assert "500 bytes" in r.json["detail"]


def test_coordinators(client):
    login("Alice")
    r = client.post("/api/campaigns", json=make_campaign_payload(
        client, name="Coordinated Contest",
        coordinator_usernames=["CoordCathy"]))
    assert r.status_code == 201, r.text
    slug = r.json["slug"]
    organizers = {m["user"]["username"] for m in r.json["members"]
                  if m["role"] == "organizer"}
    assert organizers == {"Alice", "CoordCathy"}

    # clearing the list keeps the creator as coordinator
    r = client.put(f"/api/campaigns/{slug}", json=make_campaign_payload(
        client, name="Coordinated Contest", coordinator_usernames=[]))
    assert r.status_code == 200, r.text
    organizers = {m["user"]["username"] for m in r.json["members"]
                  if m["role"] == "organizer"}
    assert organizers == {"Alice"}


def test_deactivate_campaign(client):
    login("Alice")
    r = client.post("/api/campaigns", json=make_campaign_payload(
        client, name="Deactivate Me"))
    slug = r.json["slug"]

    # drafts cannot be deactivated
    assert client.post(f"/api/campaigns/{slug}/deactivate").status_code == 400
    login("Root", is_admin=True)
    client.post(f"/api/campaigns/{slug}/approve")

    # only organizers/admins may deactivate
    login("Carol")
    assert client.post(f"/api/campaigns/{slug}/deactivate").status_code == 403

    login("Alice")
    r = client.post(f"/api/campaigns/{slug}/deactivate")
    assert r.status_code == 200 and r.json["status"] == "draft"
    # hidden from the public again
    logout()
    assert client.get(f"/api/campaigns/{slug}").status_code == 404


def test_member_management_and_admin_campaigns(client):
    login("Alice")
    r = client.post("/api/campaigns", json=make_campaign_payload(
        client, name="Member Management Contest"))
    assert r.status_code == 201, r.text
    slug = r.json["slug"]

    # organizer adds a jury member (user created on the fly)
    r = client.post(f"/api/campaigns/{slug}/members",
                    json={"username": "NewJuror", "role": "jury"})
    assert r.status_code == 201
    assert any(m["user"]["username"] == "NewJuror" and m["role"] == "jury"
               for m in r.json["members"])

    # duplicate role rejected; unknown role rejected
    assert client.post(f"/api/campaigns/{slug}/members",
                       json={"username": "NewJuror", "role": "jury"}
                       ).status_code == 409
    assert client.post(f"/api/campaigns/{slug}/members",
                       json={"username": "X", "role": "boss"}
                       ).status_code == 422

    # non-organizer cannot manage members
    login("Carol")
    assert client.post(f"/api/campaigns/{slug}/members",
                       json={"username": "Y", "role": "jury"}
                       ).status_code == 403

    # remove the juror; the last organizer is protected
    login("Alice")
    detail = client.get(f"/api/campaigns/{slug}").json
    juror = next(m for m in detail["members"]
                 if m["user"]["username"] == "NewJuror" and m["role"] == "jury")
    organizer = next(m for m in detail["members"] if m["role"] == "organizer")
    assert client.delete(
        f"/api/campaigns/{slug}/members/{organizer['id']}").status_code == 400
    r = client.delete(f"/api/campaigns/{slug}/members/{juror['id']}")
    assert r.status_code == 200
    assert not any(m["user"]["username"] == "NewJuror" and m["role"] == "jury"
                   for m in r.json["members"])

    # the admin editathon list shows every campaign with its creator
    assert client.get("/api/admin/campaigns").status_code == 403
    login("Root", is_admin=True)
    rows = client.get("/api/admin/campaigns").json
    row = next(c for c in rows if c["slug"] == slug)
    assert row["created_by_username"] == "Alice"
    assert row["status"] == "draft"


def test_participant_details_popup(client, monkeypatch):
    from datetime import datetime, timezone

    monkeypatch.setattr(
        mediawiki, "fetch_article_details",
        lambda domain, title: {
            "bytes": 20000, "words": 3100,
            "created_at": datetime(2020, 1, 2, tzinfo=timezone.utc),
            "last_updated": datetime(2026, 7, 1, tzinfo=timezone.utc),
            "qid": "Q1359020",
        })
    monkeypatch.setattr(
        mediawiki, "fetch_wikidata_details",
        lambda qid: {
            "qid": qid, "label": "Kathakali", "bytes": 900,
            "created_at": datetime(2013, 5, 5, tzinfo=timezone.utc),
            "last_updated": datetime(2026, 6, 1, tzinfo=timezone.utc),
        })

    login("Alice")
    payload = make_campaign_payload(client, name="Details Popup Contest")
    slug = client.post("/api/campaigns", json=payload).json["slug"]
    login("Root", is_admin=True)
    SYSOP_WIKIS["Root"] = {"*"}
    assert client.post(f"/api/campaigns/{slug}/approve").status_code == 200

    uid = login("Dana")
    assert client.post(f"/api/campaigns/{slug}/submissions",
                       json={"title": "Kathakali", "kind": "article"}
                       ).status_code == 201
    assert client.post(f"/api/campaigns/{slug}/submissions",
                       json={"title": "Q126", "kind": "wikidata_item"}
                       ).status_code == 201

    logout()  # endpoint is public, like the leaderboard
    rows = client.get(
        f"/api/campaigns/{slug}/participants/{uid}/details").json
    assert len(rows) == 2
    article = next(r for r in rows if r["kind"] == "article")
    assert article["details"]["words"] == 3100
    assert article["details"]["qid"] == "Q1359020"
    assert article["fetch_failed"] is False
    item = next(r for r in rows if r["kind"] == "wikidata_item")
    assert item["details"]["label"] == "Kathakali"
    assert item["details"]["bytes"] == 900

    # a failing wiki fetch flags the row instead of breaking the response
    def boom(domain, title):
        raise RuntimeError("wiki down")
    monkeypatch.setattr(mediawiki, "fetch_article_details", boom)
    rows = client.get(
        f"/api/campaigns/{slug}/participants/{uid}/details").json
    article = next(r for r in rows if r["kind"] == "article")
    assert article["fetch_failed"] is True
    assert article["details"] is None


def test_coordinator_submits_on_behalf(client):
    login("Alice")
    slug = client.post("/api/campaigns", json=make_campaign_payload(
        client, name="On Behalf Contest")).json["slug"]
    login("Root", is_admin=True)
    SYSOP_WIKIS["Root"] = {"*"}
    assert client.post(f"/api/campaigns/{slug}/approve").status_code == 200

    # a regular user cannot submit for someone else
    login("Mallory")
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"title": "Kathakali", "kind": "article",
                          "username": "Victim"})
    assert r.status_code == 403

    # a coordinator (organizer) can; the participant is auto-joined
    login("Alice")
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"title": "Kathakali", "kind": "article",
                          "username": "NewComer"})
    assert r.status_code == 201, r.text
    assert r.json["user"]["username"] == "NewComer"
    detail = client.get(f"/api/campaigns/{slug}").json
    assert any(m["user"]["username"] == "NewComer"
               and m["role"] == "participant" for m in detail["members"])

    # duplicate guard applies to the participant, not the coordinator
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"title": "Kathakali", "kind": "article",
                          "username": "NewComer"})
    assert r.status_code == 409

    # naming yourself is always allowed
    login("Mallory")
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"title": "Stub", "kind": "article",
                          "username": "Mallory"})
    assert r.status_code == 201
    assert r.json["user"]["username"] == "Mallory"


def test_coordinator_recalculates_points(client):
    login("Alice")
    slug = client.post("/api/campaigns", json=make_campaign_payload(
        client, name="Recalc Contest")).json["slug"]
    login("Root", is_admin=True)
    SYSOP_WIKIS["Root"] = {"*"}
    assert client.post(f"/api/campaigns/{slug}/approve").status_code == 200

    login("Dana")
    sub = client.post(f"/api/campaigns/{slug}/submissions",
                      json={"title": "Kathakali", "kind": "article"}).json
    # Kathakali: 5000 bytes -> 5 pts + suggested list 10 = 15
    assert sub["points"] == 15

    # participants cannot force a recalculation
    r = client.post(f"/api/submissions/{sub['id']}/recalculate")
    assert r.status_code == 403

    # an override wins until a coordinator recalculates
    login("Alice")
    r = client.post(f"/api/submissions/{sub['id']}/moderate",
                    json={"points_override": 99})
    assert r.json["points"] == 99
    r = client.post(f"/api/submissions/{sub['id']}/recalculate")
    assert r.status_code == 200
    assert r.json["points_override"] is None
    assert r.json["points"] == 15  # computed from rules and fresh metadata


def test_wikidata_bulk_submission(client, monkeypatch):
    monkeypatch.setattr(
        mediawiki, "fetch_wikidata_user_activity",
        lambda username, start, end, max_edits=None: {
            "Q100": {"statements": 12, "terms": 6},   # eligible
            "Q200": {"statements": 99, "terms": 99},  # not eligible
        })
    seen = {}
    def fake_eligible(qids, any_of):
        seen["any_of"] = any_of
        return {"Q100"}
    monkeypatch.setattr(mediawiki, "fetch_eligible_qids", fake_eligible)

    login("Alice")
    slug = client.post("/api/campaigns", json=make_campaign_payload(
        client, name="Wikidata Drive")).json["slug"]
    login("Root", is_admin=True)
    SYSOP_WIKIS["Root"] = {"*"}
    assert client.post(f"/api/campaigns/{slug}/approve").status_code == 200

    login("Dana")
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"kind": "wikidata_edits"})
    assert r.status_code == 201, r.text
    sub = r.json
    assert sub["title"] == "Wikidata edits"
    assert sub["wiki_domain"] == "www.wikidata.org"
    assert sub["metrics"]["statements"] == 12
    assert sub["metrics"]["terms"] == 6
    assert sub["metrics"]["eligible_qids"] == ["Q100"]
    # the campaign's eligibility rule constraints were passed through
    assert "P17=Q668" in seen["any_of"]
    # default rules: statements 1/5 -> 2 pts; terms 1/5 -> 1 pt
    assert sub["points"] == 3
    assert {l["label"] for l in sub["breakdown"]} == {
        "Statements added", "Labels / descriptions / aliases"}

    # only one bulk submission per participant
    assert client.post(f"/api/campaigns/{slug}/submissions",
                       json={"kind": "wikidata_edits"}).status_code == 409


def test_commons_bulk_submission_and_rule_gating(client, monkeypatch):
    monkeypatch.setattr(
        mediawiki, "fetch_commons_user_activity",
        lambda username, start, end, targets=None, max_edits=None: {
            "uploads": 4, "depicts": 7})

    login("Alice")
    slug = client.post("/api/campaigns", json=make_campaign_payload(
        client, name="Commons Drive")).json["slug"]
    login("Root", is_admin=True)
    SYSOP_WIKIS["Root"] = {"*"}
    assert client.post(f"/api/campaigns/{slug}/approve").status_code == 200

    login("Dana")
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"kind": "commons_edits"})
    assert r.status_code == 201, r.text
    sub = r.json
    assert sub["title"] == "Commons uploads"
    assert sub["metrics"] == {"uploads": 4, "depicts": 7}
    # default rules: images 1/1 (any) -> 4 pts; depicts 1/1 -> 7 pts
    assert sub["points"] == 11

    # a campaign without matching rules refuses the bulk kinds
    login("Alice")
    slug2 = client.post("/api/campaigns", json=make_campaign_payload(
        client, name="No Rules Contest", rules=[])).json["slug"]
    login("Root", is_admin=True)
    assert client.post(f"/api/campaigns/{slug2}/approve").status_code == 200
    login("Dana")
    for kind in ("wikidata_edits", "commons_edits"):
        r = client.post(f"/api/campaigns/{slug2}/submissions",
                        json={"kind": kind})
        assert r.status_code == 400, kind
    # ...and a missing title on a page submission is a clean 400
    assert client.post(f"/api/campaigns/{slug2}/submissions",
                       json={"kind": "article"}).status_code == 400


def test_bulk_over_limit_needs_manual_scoring(client, monkeypatch):
    seen = {}
    def too_many(username, start, end, max_edits=None):
        seen["max_edits"] = max_edits
        return None  # more edits than the campaign's auto-scoring cap
    monkeypatch.setattr(mediawiki, "fetch_wikidata_user_activity", too_many)

    login("Alice")
    slug = client.post("/api/campaigns", json=make_campaign_payload(
        client, name="QS Flood Contest",
        settings={"max_wikidata_edits_auto": 75})).json["slug"]
    login("Root", is_admin=True)
    SYSOP_WIKIS["Root"] = {"*"}
    assert client.post(f"/api/campaigns/{slug}/approve").status_code == 200

    login("Dana")
    r = client.post(f"/api/campaigns/{slug}/submissions",
                    json={"kind": "wikidata_edits"})
    assert r.status_code == 201, r.text
    sub = r.json
    assert seen["max_edits"] == 75          # campaign setting reached the fetcher
    assert sub["metrics"] == {"over_limit": True, "limit": 75}
    assert sub["points"] == 0               # nothing scored automatically
    assert sub["breakdown"] == []

    # the coordinator enters the points manually
    login("Alice")
    r = client.post(f"/api/submissions/{sub['id']}/moderate",
                    json={"points_override": 42})
    assert r.json["points"] == 42


def test_oauth_callback_rejection_redirects_home(client):
    # user rejected the request on meta
    r = client.get("/oauth-callback?error=unauthorized_client"
                   "&error_description=User+has+rejected+the+request")
    assert r.status_code == 302
    assert r.headers["Location"].endswith("?login=cancelled")
    # callback reached without a code at all
    r = client.get("/oauth-callback")
    assert r.status_code == 302
    assert r.headers["Location"].endswith("?login=cancelled")
    # a broken token exchange (bad state) redirects instead of 500ing
    r = client.get("/oauth-callback?code=abc&state=forged")
    assert r.status_code == 302
    assert r.headers["Location"].endswith("?login=failed")

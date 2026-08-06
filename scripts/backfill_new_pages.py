"""Re-detect is_new_page (and bytes_added) for existing submissions.

Whether a submission created its page is decided when the wiki metadata
is fetched, by comparing the page's first-revision author to the
submitter. That comparison used to be verbatim, but MediaWiki reads
underscores as spaces and capitalises the first letter — so a page whose
creator the wiki reports as "Meenakshi nandhini" did not match a stored
"Meenakshi_nandhini", and the submission was recorded as an edit to an
existing page rather than a creation. The same comparison decides which
revisions count toward bytes_added, so those rows can be short too.

The comparison is fixed (mediawiki.same_user); this re-fetches rows
recorded under the old one so their stored flags catch up. Points are
rescored from the corrected metadata as it goes.

Only article/item/file submissions are touched — bulk kinds carry no
creator. Rows are re-fetched from the MediaWiki API, so this is rate-
limited by the wiki, not the database: expect a few per second.

Safe to re-run; it only ever writes what the wiki currently reports.

Usage (from the project root):
    uv run python scripts/backfill_new_pages.py --dry-run
    uv run python scripts/backfill_new_pages.py
    uv run python scripts/backfill_new_pages.py --campaign kcm26
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domain.models import Campaign, Submission, SubmissionKind  # noqa: E402

PAGE_KINDS = (SubmissionKind.article, SubmissionKind.wikidata_item,
              SubmissionKind.commons_file)


def _arg(flag: str) -> str | None:
    if flag in sys.argv:
        index = sys.argv.index(flag)
        if index + 1 < len(sys.argv):
            return sys.argv[index + 1]
    return None


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    only_slug = _arg("--campaign")

    from core.db import SessionLocal, sync_schema
    from integrations import mediawiki
    from routers.common import rescore_submission

    sync_schema()
    db = SessionLocal()
    try:
        query = (db.query(Submission)
                 .filter(Submission.kind.in_(PAGE_KINDS))
                 .order_by(Submission.campaign_id, Submission.id))
        if only_slug:
            campaign = db.query(Campaign).filter_by(slug=only_slug).first()
            if campaign is None:
                print(f"No campaign with slug {only_slug!r}")
                return
            query = query.filter(Submission.campaign_id == campaign.id)

        # Everything the wiki fetches need is read up front, into plain
        # values. A long run makes thousands of slow API calls, and
        # ToolsDB closes a connection that has been idle for a few
        # minutes — so the session must not be held open across them, and
        # nothing inside the fetch loop may touch the database. (Reading
        # sub.user.username lazily in that loop was doing exactly that,
        # which is why a dropped connection surfaced as "fetch failed".)
        targets = [
            (s.id, s.campaign_id, s.wiki_domain, s.title, s.user.username)
            for s in query.all()
        ]
        if not targets:
            print("Nothing to do: no page submissions found.")
            return
        windows = {
            c.id: (c.slug, c.start_date, c.end_date)
            for c in db.query(Campaign).filter(
                Campaign.id.in_({t[1] for t in targets})).all()
        }
        db.commit()  # release the connection before the slow part
        print(f"Checking {len(targets)} submission(s)…")

        fetched: dict[int, object] = {}
        failed = 0
        for i, (sub_id, campaign_id, domain, title, username) in enumerate(
                targets, 1):
            window = windows.get(campaign_id)
            if window is None:
                continue
            slug, start, end = window
            try:
                meta = mediawiki.fetch_page_metadata(domain, title, username,
                                                     start, end)
            except Exception as exc:
                failed += 1
                print(f"  {slug}/{title!r}: fetch failed ({exc})")
                continue
            if meta.exists:
                fetched[sub_id] = meta
            if i % 100 == 0:
                print(f"  …{i}/{len(targets)} checked")

        # Now the database work, in short transactions over data already
        # in hand. Batched so a dropped connection costs one batch, not
        # the whole run.
        changed = 0
        batch = []
        for sub_id, meta in fetched.items():
            sub = db.get(Submission, sub_id)
            if sub is None:
                continue
            campaign = db.get(Campaign, sub.campaign_id)
            before = (sub.is_new_page, sub.bytes_added)
            after = (meta.is_new_page, meta.bytes_added)
            if before == after:
                continue
            changed += 1
            print(f"  {campaign.slug}/{sub.title!r} by {sub.user.username}: "
                  f"is_new_page {before[0]} -> {after[0]}, "
                  f"bytes_added {before[1]} -> {after[1]}")
            if dry_run:
                continue
            sub.is_new_page = meta.is_new_page
            sub.bytes_added = meta.bytes_added
            sub.page_len = meta.page_len
            sub.wikidata_qid = meta.wikidata_qid
            rescore_submission(campaign, sub)
            batch.append(sub_id)
            if len(batch) >= 50:
                db.commit()
                batch = []

        if dry_run:
            db.rollback()
            print(f"\nDry run: {changed} submission(s) would change, "
                  f"{failed} fetch failure(s). Nothing was written.")
        else:
            db.commit()
            print(f"\nUpdated {changed} submission(s), "
                  f"{failed} fetch failure(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()

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

        subs = query.all()
        if not subs:
            print("Nothing to do: no page submissions found.")
            return
        print(f"Checking {len(subs)} submission(s)…")

        # Cache the campaign per id: every submission needs its window,
        # and a campaign's settings are read again when rescoring.
        campaigns: dict[int, Campaign] = {}
        changed = failed = 0
        for i, sub in enumerate(subs, 1):
            campaign = campaigns.get(sub.campaign_id)
            if campaign is None:
                campaign = campaigns[sub.campaign_id] = db.get(
                    Campaign, sub.campaign_id)
            if campaign is None:
                continue
            try:
                meta = mediawiki.fetch_page_metadata(
                    sub.wiki_domain, sub.title, sub.user.username,
                    campaign.start_date, campaign.end_date)
            except Exception as exc:
                failed += 1
                print(f"  {campaign.slug}/{sub.title!r}: fetch failed ({exc})")
                continue
            if not meta.exists:
                continue

            before = (sub.is_new_page, sub.bytes_added)
            after = (meta.is_new_page, meta.bytes_added)
            if before == after:
                continue
            changed += 1
            print(f"  {campaign.slug}/{sub.title!r} by {sub.user.username}: "
                  f"is_new_page {before[0]} -> {after[0]}, "
                  f"bytes_added {before[1]} -> {after[1]}")
            if not dry_run:
                sub.is_new_page = meta.is_new_page
                sub.bytes_added = meta.bytes_added
                sub.page_len = meta.page_len
                sub.wikidata_qid = meta.wikidata_qid
                rescore_submission(campaign, sub)
                # Committed in batches: a long run should not hold one
                # transaction open across thousands of wiki round-trips.
                if changed % 50 == 0:
                    db.commit()
            if i % 100 == 0:
                print(f"  …{i}/{len(subs)} checked")

        if dry_run:
            print(f"\nDry run: {changed} submission(s) would change, "
                  f"{failed} fetch failure(s). Nothing was written.")
            db.rollback()
        else:
            db.commit()
            print(f"\nUpdated {changed} submission(s), "
                  f"{failed} fetch failure(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()

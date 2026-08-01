"""Resolve the connected Wikidata item for existing suggested articles.

Suggested articles are matched to submissions by QID, and that QID is
resolved when a campaign's list is saved. Lists saved before that was
introduced have an empty qid, so their bonus cannot match until someone
re-saves the campaign — this backfills them in one pass instead.

Safe to re-run: it only fills rows whose qid is still empty, and never
clears one that is already set. Articles with no connected item stay
empty (nothing to resolve) and are reported at the end.

Usage (from the project root):
    uv run python scripts/backfill_suggested_qids.py --dry-run
    uv run python scripts/backfill_suggested_qids.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domain.models import Campaign, SubmissionKind, SuggestedPage  # noqa: E402
from domain.scoring import normalize_title  # noqa: E402


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    from core.db import SessionLocal, sync_schema
    from integrations import mediawiki

    # The qid column is added by sync_schema (which the app runs at
    # startup); do it here too so this script works before the next
    # deploy restarts the app.
    sync_schema()

    db = SessionLocal()
    try:
        pending = (db.query(SuggestedPage)
                   .filter(SuggestedPage.kind == SubmissionKind.article,
                           SuggestedPage.qid == "")
                   .all())
        if not pending:
            print("Nothing to do: every suggested article already has a QID.")
            return

        # One API call per wiki, batched 50 titles at a time by
        # fetch_wikibase_items, rather than one call per article.
        by_campaign: dict[int, list[SuggestedPage]] = {}
        for page in pending:
            by_campaign.setdefault(page.campaign_id, []).append(page)

        resolved = unresolved = 0
        for campaign_id, pages in by_campaign.items():
            campaign = db.get(Campaign, campaign_id)
            if campaign is None:
                continue
            try:
                found = mediawiki.fetch_wikibase_items(
                    campaign.wiki_domain, [p.title for p in pages])
            except Exception as exc:
                print(f"  {campaign.slug}: lookup failed ({exc}) — skipped")
                continue
            by_norm = {normalize_title(t): q for t, q in found.items()}
            hits = 0
            for page in pages:
                qid = by_norm.get(normalize_title(page.title))
                if qid:
                    if not dry_run:
                        page.qid = qid
                    hits += 1
                else:
                    unresolved += 1
                    print(f"  {campaign.slug}: no Wikidata item for "
                          f"{page.title!r}")
            resolved += hits
            print(f"{campaign.slug} ({campaign.wiki_domain}): "
                  f"{hits}/{len(pages)} resolved")

        if dry_run:
            print(f"\nDry run: would set {resolved} QID(s); "
                  f"{unresolved} article(s) have no connected item.")
        else:
            db.commit()
            print(f"\nSet {resolved} QID(s); "
                  f"{unresolved} article(s) have no connected item.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

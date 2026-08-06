"""Recalculate submission points from the command line.

Two different jobs share the word "recalculate", and this script keeps
them separate because their costs differ by orders of magnitude:

  (default)   rescore from data already in the database. Pure computation
              over the campaign's rules, settings, suggested list, claims
              and reviews — no network, thousands of rows a second. This
              is what to run after editing scoring rules, changing a
              setting, or fixing a suggested list, and to repair any
              cached total that drifted.

  --refetch   fetch each page's metadata from the MediaWiki API first,
              then rescore. This is the expensive one (several round
              trips per submission, rate-limited by the wiki) and is only
              needed when the stored wiki data itself is stale — e.g.
              participants kept editing after submitting.

Points live on the submission row (points_cached) and every write path in
the app keeps them fresh, so the default mode is normally a no-op that
simply confirms agreement. It exists so scoring can be driven from a cron
job or a shell rather than by someone clicking through the UI, and so a
campaign can be re-scored in bulk without touching the frontend at all.

The scoring engine is not reimplemented here: it calls the same
compute_breakdown the API uses, through routers.common.rescore_*.

Safe to re-run; it is deterministic given the same inputs.

Usage (from the project root):
    uv run python scripts/recalculate_scores.py --dry-run
    uv run python scripts/recalculate_scores.py --campaign kcm26
    uv run python scripts/recalculate_scores.py --active
    uv run python scripts/recalculate_scores.py --campaign kcm26 --refetch
    uv run python scripts/recalculate_scores.py --campaign kcm26 --refetch --user Dana
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domain.models import (Campaign, CampaignStatus, Submission,  # noqa: E402
                           SubmissionKind)

# Bulk kinds are scored from counted activity, not page metadata; their
# refresh is scripts/recalculate_bulk.py, which walks contribution
# histories instead of page histories.
PAGE_KINDS = (SubmissionKind.article, SubmissionKind.wikidata_item,
              SubmissionKind.commons_file)


def _arg(flag: str, default: str | None = None) -> str | None:
    if flag in sys.argv:
        index = sys.argv.index(flag)
        if index + 1 < len(sys.argv):
            return sys.argv[index + 1]
    return default


def _campaigns(db, only_slug: str | None, active_only: bool) -> list[Campaign]:
    query = db.query(Campaign).order_by(Campaign.start_date.desc())
    if only_slug:
        query = query.filter(Campaign.slug == only_slug)
    if active_only:
        query = query.filter(Campaign.status == CampaignStatus.active)
    return query.all()


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    refetch = "--refetch" in sys.argv
    only_slug = _arg("--campaign")
    only_user = _arg("--user")
    active_only = "--active" in sys.argv

    from core.db import SessionLocal, sync_schema
    from routers.common import (load_submissions, rescore_submission,
                                suggested_titles)
    from domain.scoring import compute_breakdown

    sync_schema()
    db = SessionLocal()
    try:
        campaigns = _campaigns(db, only_slug, active_only)
        if not campaigns:
            print("No campaign matches." if only_slug or active_only
                  else "No campaigns found.")
            return
        if only_user and not refetch:
            # Rescoring is per-campaign by design (it reuses one settings
            # and suggested-key set for the whole run); narrowing it to a
            # single participant would save nothing measurable.
            print("--user applies to --refetch only; ignoring it.")
            only_user = None

        total_changed = total_seen = total_failed = 0
        for campaign in campaigns:
            subs = load_submissions(db, campaign.id)
            if only_user:
                subs = [s for s in subs if s.user.username == only_user]
            if not subs:
                continue

            if refetch:
                from routers.submissions import _fetch_metadata

                page_subs = [s for s in subs if s.kind in PAGE_KINDS]
                print(f"{campaign.slug}: refetching wiki metadata for "
                      f"{len(page_subs)} submission(s)…")
                for i, sub in enumerate(page_subs, 1):
                    try:
                        _fetch_metadata(sub, campaign, sub.user.username)
                    except Exception as exc:
                        total_failed += 1
                        print(f"  {sub.title!r}: fetch failed ({exc})")
                    if i % 100 == 0:
                        print(f"  …{i}/{len(page_subs)}")

            # Rescore against the campaign's current rules and settings.
            # The suggested-list key set is built once per kind rather than
            # once per submission — it is the same set for every row of a
            # kind, and rebuilding it per row is what made the old
            # request-time scoring quadratic on large campaigns.
            settings = campaign.effective_settings
            keys_by_kind: dict[SubmissionKind, set[str]] = {}
            changed = 0
            for sub in subs:
                keys = keys_by_kind.get(sub.kind)
                if keys is None:
                    keys = keys_by_kind[sub.kind] = suggested_titles(
                        campaign, sub.kind)
                before = (float(sub.points_cached)
                          if sub.points_cached is not None else None)
                after = compute_breakdown(sub, campaign.rules, keys,
                                          campaign.scoring_mode, settings).total
                total_seen += 1
                if before is not None and abs(after - before) < 0.005:
                    continue
                changed += 1
                shown = "unscored" if before is None else before
                print(f"  {campaign.slug}/{sub.title!r} "
                      f"by {sub.user.username}: {shown} -> {after}")
                if not dry_run:
                    sub.points_cached = after
            total_changed += changed

            board_note = ""
            if changed:
                board_note = f" — {changed} changed"
            print(f"{campaign.slug}: {len(subs)} submission(s){board_note}")

        if dry_run:
            db.rollback()
            print(f"\nDry run: {total_changed} of {total_seen} submission(s) "
                  f"would change, {total_failed} fetch failure(s). "
                  "Nothing was written.")
        else:
            db.commit()
            print(f"\nRescored {total_seen} submission(s), "
                  f"{total_changed} changed, {total_failed} fetch failure(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()

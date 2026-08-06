"""Recalculate Wikidata / Commons bulk submissions from the command line.

A bulk submission counts one participant's whole activity in the campaign
window, which means walking their contribution history 500 revisions per
request. The web sweep ("Recalculate all") has to answer inside one HTTP
request, so it runs against the *lower* max_wikidata_edits_sweep cap and
skips anyone above it — on a large campaign that leaves the heaviest
contributors permanently unscored until someone recalculates each of them
by hand.

This script has no request deadline, so it uses the generous
wikidata_edit_limit_single cap instead and can score those participants.
Run it from a cron job (or by hand after a campaign closes) and the
result is already in the database before anyone opens the page.

The counting itself is not reimplemented here: it calls the same
_fetch_bulk_metrics the API uses, so the two can never disagree about
what an edit is worth. Points are rescored from the fresh metrics.

Safe to re-run: it only ever writes what the wiki currently reports.

Usage (from the project root):
    uv run python scripts/recalculate_bulk.py --dry-run
    uv run python scripts/recalculate_bulk.py --campaign kcm26
    uv run python scripts/recalculate_bulk.py --campaign kcm26 --user Dana
    uv run python scripts/recalculate_bulk.py --kind commons_edits
    uv run python scripts/recalculate_bulk.py --active          # running only
    uv run python scripts/recalculate_bulk.py --workers 8
"""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domain.models import (Campaign, CampaignStatus, Submission,  # noqa: E402
                           SubmissionKind)

BULK_KINDS = (SubmissionKind.wikidata_edits, SubmissionKind.commons_edits)


def _arg(flag: str, default: str | None = None) -> str | None:
    if flag in sys.argv:
        index = sys.argv.index(flag)
        if index + 1 < len(sys.argv):
            return sys.argv[index + 1]
    return default


def _describe(metrics: dict | None) -> str:
    if not metrics:
        return "no counts"
    if metrics.get("over_limit"):
        return f"over {metrics.get('limit')} edits — needs a manual override"
    if "uploads" in metrics:
        return (f"{metrics.get('uploads', 0)} uploads, "
                f"{metrics.get('depicts', 0)} depicts")
    return (f"{metrics.get('statements', 0)} statements, "
            f"{metrics.get('terms', 0)} terms, "
            f"{len(metrics.get('eligible_qids') or [])}"
            f"/{metrics.get('edited_qids', 0)} items eligible")


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    only_slug = _arg("--campaign")
    only_user = _arg("--user")
    only_kind = _arg("--kind")
    active_only = "--active" in sys.argv
    try:
        workers = max(1, min(16, int(_arg("--workers", "4"))))
    except ValueError:
        print("--workers takes a number")
        return

    from core.db import SessionLocal, sync_schema
    from routers.common import rescore_submission
    from routers.submissions import (_fetch_bulk_metrics,
                                     _individually_submitted_qids)

    sync_schema()
    db = SessionLocal()
    try:
        query = (db.query(Submission)
                 .filter(Submission.kind.in_(BULK_KINDS))
                 .order_by(Submission.campaign_id, Submission.id))
        if only_kind:
            try:
                query = query.filter(Submission.kind == SubmissionKind(only_kind))
            except ValueError:
                print(f"--kind must be one of: "
                      f"{', '.join(k.value for k in BULK_KINDS)}")
                return
        if only_slug:
            campaign = db.query(Campaign).filter_by(slug=only_slug).first()
            if campaign is None:
                print(f"No campaign with slug {only_slug!r}")
                return
            query = query.filter(Submission.campaign_id == campaign.id)
        if active_only:
            query = query.filter(Submission.campaign_id.in_(
                db.query(Campaign.id)
                .filter(Campaign.status == CampaignStatus.active)))

        subs = query.all()
        if only_user:
            subs = [s for s in subs if s.user.username == only_user]
        if not subs:
            print("Nothing to do: no matching bulk submissions.")
            return

        campaigns: dict[int, Campaign] = {}
        for sub in subs:
            if sub.campaign_id not in campaigns:
                campaigns[sub.campaign_id] = db.get(Campaign, sub.campaign_id)
        print(f"Recalculating {len(subs)} bulk submission(s) across "
              f"{len(campaigns)} campaign(s), {workers} at a time…")

        # Everything the fetches need is resolved on this thread, before
        # the pool starts: a Session is not thread-safe, and the fetches
        # take minutes, which is long enough for ToolsDB to drop an idle
        # connection and poison a session held open across them.
        #
        # _fetch_bulk_metrics normally takes the session so it can exclude
        # items the participant submitted individually. That query is run
        # here instead and the answer passed in as a stub, so the workers
        # get the same exclusion without touching the database.
        plan = []
        for sub in subs:
            own = _individually_submitted_qids(
                db, campaigns[sub.campaign_id], sub.user_id)
            plan.append((sub.id, sub.campaign_id, sub.user_id, sub.kind,
                         sub.title, sub.wiki_domain, sub.user.username, own))
        db.commit()  # release the connection before the slow part

        class _OwnQids:
            """Stands in for the session inside the worker: answers the one
            query _fetch_bulk_metrics makes, from the set resolved above."""

            def __init__(self, qids: set[str]):
                self._qids = qids

            def query(self, *args, **kwargs):
                return self

            def filter(self, *args, **kwargs):
                return self

            def all(self):
                return [(q,) for q in self._qids]

        def fetch(item) -> tuple[int, dict | None, str]:
            (sub_id, campaign_id, user_id, kind, title, domain,
             username, own) = item
            campaign = campaigns[campaign_id]
            probe = Submission(campaign_id=campaign_id, user_id=user_id,
                               kind=kind, title=title, wiki_domain=domain)
            try:
                _fetch_bulk_metrics(probe, campaign, username, _OwnQids(own))
                return sub_id, probe.metrics, ""
            except Exception as exc:
                return sub_id, None, str(exc)

        results: dict[int, tuple[dict | None, str]] = {}
        with ThreadPoolExecutor(max_workers=min(workers, len(plan))) as pool:
            for sub_id, metrics, err in pool.map(fetch, plan):
                results[sub_id] = (metrics, err)

        changed = unchanged = failed = capped = 0
        for sub in subs:
            campaign = campaigns[sub.campaign_id]
            metrics, err = results[sub.id]
            label = f"{campaign.slug}/{sub.user.username}"
            if err:
                failed += 1
                print(f"  {label}: fetch failed ({err})")
                continue
            if metrics is None:
                # _fetch_bulk_metrics swallows its own errors and leaves the
                # metrics untouched; nothing was measured, so nothing is written.
                failed += 1
                print(f"  {label}: no counts returned — left unchanged")
                continue
            if metrics.get("over_limit"):
                capped += 1
            if metrics == sub.metrics:
                unchanged += 1
                continue
            changed += 1
            print(f"  {label}: {_describe(sub.metrics)} -> {_describe(metrics)}")
            if not dry_run:
                from datetime import datetime, timezone

                sub.metrics = metrics
                sub.metadata_fetched_at = datetime.now(timezone.utc)
                rescore_submission(campaign, sub)

        if dry_run:
            db.rollback()
            print(f"\nDry run: {changed} would change, {unchanged} unchanged, "
                  f"{capped} over the cap, {failed} failed. Nothing written.")
        else:
            db.commit()
            print(f"\nUpdated {changed}, {unchanged} unchanged, "
                  f"{capped} over the cap (need a manual points override), "
                  f"{failed} failed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

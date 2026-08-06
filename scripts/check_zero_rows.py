"""Run ON TOOLFORGE. Reports exactly what the DB holds and what the wiki
returns for the one row that changed is_new_page, without writing anything."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from core.db import SessionLocal
from domain.models import Campaign, Submission
from integrations import mediawiki

db = SessionLocal()
c = db.query(Campaign).filter_by(slug='kcm26').first()
rows = (db.query(Submission)
        .filter(Submission.campaign_id == c.id,
                Submission.is_new_page.is_(False),
                Submission.bytes_added == 0)
        .all())
print(f"{len(rows)} submission(s) stored as 'not new, 0 bytes':\n")
for s in rows:
    meta = None
    try:
        meta = mediawiki.fetch_page_metadata(
            s.wiki_domain, s.title, s.user.username, c.start_date, c.end_date)
    except Exception as exc:
        print(f"  id={s.id} {s.title!r} @ {s.wiki_domain}: fetch error {exc}")
        continue
    print(f"  id={s.id} {s.title!r}")
    print(f"      wiki={s.wiki_domain} user={s.user.username!r} kind={s.kind.value}")
    print(f"      stored: is_new={s.is_new_page} bytes={s.bytes_added} points={s.points_cached}")
    print(f"      wiki  : exists={meta.exists} creator={meta.creator!r} "
          f"is_new={meta.is_new_page} bytes={meta.bytes_added} len={meta.page_len}")
db.close()

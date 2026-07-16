# WikiSTAR

Submission, review and self-assessment tool for Wikipedia/Wikidata
editathons and writing contests.

> **v2 rewrite in progress.** The previous Flask implementation lives on
> the [`legacy-v1`](../../tree/legacy-v1) branch. See
> [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full schema and
> design.

## What it does

* **Organizers** create campaigns: dates, target wiki, scoring mode,
  configurable point rules, jury members and suggested page lists.
* **Participants** log in with their Wikimedia account and submit
  articles or Wikidata items. Page metadata (bytes added, new-page
  detection) is verified against the MediaWiki API.
* **Juries** score submissions (jury mode), or verify participants'
  point claims (self-assessment / hybrid modes).

### Scoring modes

| Mode | Who counts the points |
|---|---|
| `jury` | Jurors review every submission; points = average of accepting reviews |
| `self` | Participants claim points under the campaign's configurable rules; organizers verify/adjust and always have the final say |
| `hybrid` | Self-assessment claims + jury verification |

The point rules (e.g. *+1 per 1,000 bytes, +2 substantial improvement,
+10 suggested article, +25 Good Article, Wikidata item/statement/label/
reference points, 3,500-byte minimum for new articles*) are stored per
campaign and fully editable; a default preset ships with the tool.

## Stack

Flask · SQLAlchemy 2.0 · MariaDB · MediaWiki OAuth 2.0
(Authlib) · Vue 3 · Vite · Pinia · Tailwind CSS 4

The FastAPI/ASGI variant of this backend is preserved on the
[`archive/fastapi-v2`](../../tree/archive/fastapi-v2) branch.

## Development

```bash
# backend (Python 3.12, uv)
cp config.toml.example config.toml   # fill in OAuth credentials
uv sync
uv run flask --app app run --debug --port 8000   # http://localhost:8000

# frontend
cd frontend
npm install
npm run dev                                   # http://localhost:5173, proxies /api

# tests
uv run pytest

# drop the configured database and recreate the schema from scratch
uv run python reset_db.py
```

## Deployment (Toolforge)

Classic python webservice (uwsgi). The repository root is the
webservice source directory; Flask serves the built frontend from
`frontend/dist` (`npm run build`).

```bash
become wikistar
git clone https://gitlab.wikimedia.org/toolforge-repos/wikistar.git ~/www/python/src
# build uwsgi's venv inside the webservice shell, with the image's own
# python3 (must match uwsgi's Python), then install deps with uv
webservice python3.13 shell
rm -rf ~/www/python/venv && python3 -m venv ~/www/python/venv
cd ~/www/python/src
uv pip install --python ~/www/python/venv/bin/python -r pyproject.toml
cp ~/www/python/src/uwsgi.ini ~/www/python/uwsgi.ini   # larger buffer for OAuth callbacks
exit
webservice python3.13 restart
```

uwsgi serves the `app` callable in `app.py` directly (the default);
`application` is provided as an alias. Configuration comes from
environment variables or `~/www/python/src/config.toml` (SECRET_KEY,
DATABASE_URL for ToolsDB, CONSUMER_KEY/CONSUMER_SECRET,
SESSION_COOKIE_SECURE=true).

OAuth consumer registration:
<https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration>
(see [MEDIAWIKI_OAUTH_GUIDE.md](MEDIAWIKI_OAUTH_GUIDE.md)).

## License

See [LICENSE](LICENSE).

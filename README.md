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

FastAPI · SQLAlchemy 2.0 · MariaDB (SQLite in dev) · MediaWiki OAuth 2.0
(Authlib) · Vue 3 · Vite · Pinia · Bootstrap 5

## Development

```bash
# backend (Python 3.12, uv)
cp config.toml.example config.toml   # fill in OAuth credentials
uv sync
uv run uvicorn backend.main:app --reload   # http://localhost:8000, docs at /docs

# frontend
cd frontend
pnpm install
pnpm dev                                   # http://localhost:5173, proxies /api

# tests
uv run pytest
```

## Deployment (Toolforge)

Build the frontend (`pnpm build`) — FastAPI serves `frontend/dist` —
and run the ASGI app with uvicorn. OAuth consumer registration:
<https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration>
(see [MEDIAWIKI_OAUTH_GUIDE.md](MEDIAWIKI_OAUTH_GUIDE.md)).

## License

See [LICENSE](LICENSE).

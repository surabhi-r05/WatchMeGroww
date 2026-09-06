# Watch Me Groww

An India-first market intelligence/watchlist app for the Groww hackathon.

## Demo accounts

- demo@watchmegroww.app / demo1234
- admin@watchmegroww.app / admin1234

## Run locally

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### Deploy to Vercel

Push the repository to GitHub, import it as a Vercel project, and keep the
project root at the repository root. The included `vercel.json` builds the
Vite app from `frontend/` and routes `/api/*` to the FastAPI function in
`api/index.py`.

Add these Vercel environment variables for the Preview and Production
environments:

```text
DEMO_MODE=true
DATABASE_URL=sqlite:///./watchmegroww.db
GNEWS_API_KEY=your_key
```

Do not commit real API keys. The deployed frontend uses `/api` automatically;
for local development, copy `frontend/.env.example` to `frontend/.env`.

SQLite storage on Vercel is ephemeral. This is suitable for a demo, but a
production deployment should later use a hosted database.

## Real news

Set `GNEWS_API_KEY` in a backend `.env` file. The backend fetches verified article metadata server-side and caches it. The UI labels the freshness and never invents news when the provider is unavailable.

The free GNews plan is intended for development/testing and has a 12-hour delay and 100 requests/day. For a published production application, use a plan/provider whose license fits the deployment.

## Data reliability

- Demo market data is explicitly labelled demo.
- News is separately labelled verified/provider-backed, cached, delayed, unavailable or error.
- Watchlists, notes, alerts and last-seen baselines live in the database, so signing into the same account on another device restores the same state.
- Redis can be enabled for shared caching when scaling beyond one application process.
- Alert evaluation runs server-side on a scheduler, with a 15-minute duplicate cooldown.
- Database queries use indexes and bounded result sizes.

## Bear icon

Place your existing `bear.png` at:

`frontend/public/bear.png`

The UI references `/bear.png` for the brand icon and gracefully hides it if it is absent.

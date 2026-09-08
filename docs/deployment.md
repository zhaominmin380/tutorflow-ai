# TutorFlow Deployment Notes

## Local development with Docker Compose

Docker Compose is the reproducible local-development environment. It starts a
Postgres database, a FastAPI service with backend reload enabled, and the Vite
development server with frontend hot-module replacement. It is not the Railway
deployment configuration.

1. Install Docker Desktop (or Docker Engine with the Compose plugin).
2. If you do not already have a local `.env`, copy the safe local defaults and
   adjust them for your machine:

   ```sh
   cp .env.example .env
   ```

   When adapting an existing non-Docker `.env`, set `DATABASE_URL` to the
   `postgres` service hostname as shown in `.env.example`, rather than
   `localhost`.

3. Start the complete local stack:

   ```sh
   docker compose up --build
   ```

Open the development UI at `http://localhost:5173`. The API and its Swagger UI
are available at `http://localhost:8000` and `http://localhost:8000/docs`.
The frontend proxies `/api` requests to the API container, so no browser API URL
configuration is necessary.

If one of the default host ports is already occupied, change `POSTGRES_PORT`,
`API_PORT`, or `FRONTEND_PORT` in `.env`; the corresponding container ports stay
at `5432`, `8000`, and `5173`.

Source changes under `frontend/tutorflow-ai` and `backend` reload automatically.
After changing backend dependencies or the root `Dockerfile`, rebuild the API
image with `docker compose up --build api`. Compose persists database data in its
`postgres_data` volume. Use `docker compose down -v` only when intentionally
discarding all local database data.

The local defaults are intentionally non-production values. Do not reuse the
local `SECRET_KEY`, Postgres password, or `.env` file for Railway. Railway
continues to use the root `Dockerfile` and `railway.toml` described below.

## Railway MVP deployment

TutorFlow deploys as one Railway web service plus Railway Postgres. The web service
serves the React application and FastAPI from the same domain, so the browser keeps
using its existing `/api/v1` requests without a CORS or API-base-URL configuration.

### Deploy the web service

1. Merge the release commit into the branch you intend to deploy, normally `master`.
2. In Railway, create a project and add **PostgreSQL**. Keep its service name as
   `Postgres` for the variable reference below.
3. Add a service from this GitHub repository. Its root directory must be the
   repository root, where `Dockerfile` and `railway.toml` live.
4. In the web service's Variables tab, add the following values. Do not upload the
   local `.env` file.

   ```env
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   SECRET_KEY=<a newly generated random secret>
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   AI_BASE_URL=https://api.openai.com/v1
   AI_API_KEY=<a newly rotated OpenAI API key>
   AI_MODEL=gpt-5.4-mini
   AI_TIMEOUT_SECONDS=30
   AI_MAX_RETRIES=2
   AI_LOG_RETENTION_DAYS=90
   AI_DATA_PROCESSING_CONSENT_CONFIRMED=false
   ```

   `DATABASE_URL` uses Railway's private Postgres connection. The application
   normalizes Railway's standard PostgreSQL URL to the installed `psycopg` driver.
   Change `AI_DATA_PROCESSING_CONSENT_CONFIRMED` to `true` only after the required
   disclosure and consent have been obtained.
5. Deploy. The Docker image builds the frontend, runs `alembic upgrade head`, and
   then starts FastAPI on Railway's injected `PORT`. `railway.toml` makes
   `/health/db` the deployment health check, so Railway only routes traffic after
   the database is reachable.
6. Generate a Railway domain and verify all three endpoints:

   ```text
   /
   /health
   /health/db
   ```

   Then register a test Tutor, create a Student, schedule a Lesson, and create a
   Lesson record before inviting any real users.

### Required launch operations

- Rotate the local OpenAI key and JWT `SECRET_KEY` before setting Railway variables.
  The existing `.env` is ignored by Git and must remain local.
- Set a Railway usage hard limit of **US$20** for the pilot, with a lower soft alert.
- Enable a Postgres backup/restore process before storing real Tutor data.
- Add a second Railway service from this repository for daily AI-log retention.
  Give it the same `DATABASE_URL` reference, set its Start Command to
  `python -m app.maintenance`, do not generate a public domain, disable its health
  check, and configure cron `0 19 * * *`. Railway evaluates cron in UTC, which is
  03:00 Asia/Taipei on the following calendar day.

## Database Migration Gate

The application startup creates missing tables for local development, but `Base.metadata.create_all()` does not upgrade existing tables. Run the migration before starting a deployment that contains database changes:

```powershell
cd C:\Users\dcyin\Desktop\files\tutorflow-ai\backend
alembic upgrade head
alembic current
```

The command must use the same `DATABASE_URL` as the application. For the current Sprint 8 release, the target revision is `20260811_0003`. The API should not receive production traffic until the migration succeeds.

## AI Provider Consent

Keep the external provider disabled until the product has disclosed the data transfer and obtained the required consent. Enable it explicitly with:

```env
AI_DATA_PROCESSING_CONSENT_CONFIRMED=true
```

This is a deployment-level gate for Sprint 7. A future per-user consent workflow should replace it before enabling AI for tenants with different consent states.

## AI Log Retention

AI Logs can contain lesson notes and provider responses. The default retention period is 90 days and can be changed with `AI_LOG_RETENTION_DAYS`.

Run the cleanup command daily from the `backend` directory:

```powershell
python -m app.maintenance
```

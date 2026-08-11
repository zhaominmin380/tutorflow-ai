# TutorFlow Deployment Notes

## Database Migration Gate

The application startup creates missing tables for local development, but `Base.metadata.create_all()` does not upgrade existing tables. Run the migration before starting a deployment that contains database changes:

```powershell
cd C:\Users\dcyin\Desktop\files\tutorflow-ai\backend
alembic upgrade head
alembic current
```

The command must use the same `DATABASE_URL` as the application. For Sprint 7, the target revision is `20260803_0002`. The API should not receive production traffic until the migration succeeds.

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

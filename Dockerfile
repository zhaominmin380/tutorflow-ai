FROM node:22-alpine AS frontend-build

WORKDIR /build/frontend
COPY frontend/tutorflow-ai/package.json frontend/tutorflow-ai/package-lock.json ./
RUN npm ci
COPY frontend/tutorflow-ai/ ./
RUN npm run build

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FRONTEND_DIST=/app/frontend/dist \
    DATABASE_SCHEMA_MANAGED_BY_ALEMBIC=true

WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /build/frontend/dist /app/frontend/dist

RUN useradd --create-home --uid 10001 tutorflow \
    && chown -R tutorflow:tutorflow /app
USER tutorflow

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

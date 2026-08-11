from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AuthSettings:
    secret_key: str | None = os.getenv("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    def require_secret_key(self) -> str:
        if not self.secret_key:
            raise RuntimeError("SECRET_KEY must be configured.")
        return self.secret_key


settings = AuthSettings()


@dataclass(frozen=True)
class AISettings:
    base_url: str | None = os.getenv("AI_BASE_URL")
    api_key: str | None = os.getenv("AI_API_KEY")
    model: str = os.getenv("AI_MODEL", "gpt-4.1-mini")
    timeout_seconds: float = float(os.getenv("AI_TIMEOUT_SECONDS", "20"))
    max_retries: int = int(os.getenv("AI_MAX_RETRIES", "1"))
    log_retention_days: int = int(os.getenv("AI_LOG_RETENTION_DAYS", "90"))
    data_processing_consent_confirmed: bool = (
        os.getenv("AI_DATA_PROCESSING_CONSENT_CONFIRMED", "false").lower() == "true"
    )

    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def is_enabled(self) -> bool:
        return self.is_configured() and self.data_processing_consent_confirmed


ai_settings = AISettings()

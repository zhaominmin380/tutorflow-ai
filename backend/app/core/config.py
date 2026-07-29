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

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

import httpx

from app.core.config import ai_settings


@dataclass(frozen=True)
class AIProviderResult:
    provider: str
    model: str
    content: str
    duration_ms: int


class AIProviderError(Exception):
    status_code = 502

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        model: str = "unknown",
        upstream_status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.upstream_status_code = upstream_status_code


class AIProviderConfigurationError(AIProviderError):
    status_code = 503


class AIProviderTimeoutError(AIProviderError):
    status_code = 504


class AIProviderRateLimitError(AIProviderError):
    status_code = 503


class AIProviderUpstreamError(AIProviderError):
    status_code = 502


class AIProviderInvalidOutputError(AIProviderError):
    status_code = 502


class AIProvider(Protocol):
    provider_name: str
    model_name: str

    def generate(self, prompt: str, response_schema: dict[str, object] | None = None) -> AIProviderResult:
        ...


class OpenAICompatibleProvider:
    provider_name = "openai_compatible"

    def __init__(self) -> None:
        self.model_name = ai_settings.model

    def generate(self, prompt: str, response_schema: dict[str, object] | None = None) -> AIProviderResult:
        if not ai_settings.is_configured():
            raise AIProviderConfigurationError(
                "AI provider is not configured.",
                provider=self.provider_name,
                model=self.model_name,
            )
        if not ai_settings.data_processing_consent_confirmed:
            raise AIProviderConfigurationError(
                "AI provider is disabled until data processing consent is confirmed.",
                provider=self.provider_name,
                model=self.model_name,
            )

        endpoint = f"{ai_settings.base_url.rstrip('/')}/chat/completions"
        payload: dict[str, object] = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        if response_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "lesson_summary",
                    "strict": True,
                    "schema": response_schema,
                },
            }
        elif response_schema is not None:
            payload["response_format"] = {"type": "json_object"}

        started_at = perf_counter()
        for attempt in range(ai_settings.max_retries + 1):
            try:
                with httpx.Client(timeout=ai_settings.timeout_seconds) as client:
                    response = client.post(
                        endpoint,
                        headers={"Authorization": f"Bearer {ai_settings.api_key}"},
                        json=payload,
                    )
            except httpx.TimeoutException as exc:
                if attempt < ai_settings.max_retries:
                    continue
                raise AIProviderTimeoutError(
                    "AI provider request timed out.",
                    provider=self.provider_name,
                    model=self.model_name,
                ) from exc
            except httpx.HTTPError as exc:
                if attempt < ai_settings.max_retries:
                    continue
                raise AIProviderUpstreamError(
                    "AI provider request failed.",
                    provider=self.provider_name,
                    model=self.model_name,
                ) from exc

            if response.status_code == 429:
                raise AIProviderRateLimitError(
                    "AI provider rate limit reached.",
                    provider=self.provider_name,
                    model=self.model_name,
                    upstream_status_code=response.status_code,
                )
            if response.status_code >= 500:
                if attempt < ai_settings.max_retries:
                    continue
                raise AIProviderUpstreamError(
                    f"AI provider is unavailable (HTTP {response.status_code}).",
                    provider=self.provider_name,
                    model=self.model_name,
                    upstream_status_code=response.status_code,
                )
            if response.is_error:
                if response.status_code in {401, 403}:
                    raise AIProviderConfigurationError(
                        f"AI provider authentication or permission failed (HTTP {response.status_code}).",
                        provider=self.provider_name,
                        model=self.model_name,
                        upstream_status_code=response.status_code,
                    )
                raise AIProviderUpstreamError(
                    f"AI provider rejected the request (HTTP {response.status_code}).",
                    provider=self.provider_name,
                    model=self.model_name,
                    upstream_status_code=response.status_code,
                )

            try:
                content = response.json()["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise AIProviderInvalidOutputError(
                    "AI provider returned an invalid response.",
                    provider=self.provider_name,
                    model=self.model_name,
                ) from exc

            if not isinstance(content, str) or not content.strip():
                raise AIProviderInvalidOutputError(
                    "AI provider returned an empty response.",
                    provider=self.provider_name,
                    model=self.model_name,
                )

            return AIProviderResult(
                provider=self.provider_name,
                model=self.model_name,
                content=content,
                duration_ms=round((perf_counter() - started_at) * 1000),
            )

        raise AIProviderUpstreamError("AI provider request failed.", self.provider_name, self.model_name)

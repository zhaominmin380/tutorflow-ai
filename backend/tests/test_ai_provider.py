from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from typing_extensions import Self

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.ai_provider import (
    AIProviderConfigurationError,
    AIProviderUpstreamError,
    OpenAICompatibleProvider,
)


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        self.is_error = status_code >= 400


class FakeClient:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.payload: dict[str, object] | None = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def post(self, endpoint: str, headers: dict[str, str], json: dict[str, object]) -> FakeResponse:
        self.payload = json
        return self.response


def configured_settings(consent_confirmed: bool) -> SimpleNamespace:
    return SimpleNamespace(
        base_url="https://provider.example/v1",
        api_key="test-key",
        model="test-model",
        timeout_seconds=1,
        max_retries=0,
        data_processing_consent_confirmed=consent_confirmed,
        is_configured=lambda: True,
    )


class AIProviderTest(unittest.TestCase):
    def test_provider_requires_data_processing_consent(self) -> None:
        with (
            patch("app.services.ai_provider.ai_settings", configured_settings(False)),
            self.assertRaises(AIProviderConfigurationError) as context,
        ):
            OpenAICompatibleProvider().generate("test prompt")

        self.assertIn("consent", str(context.exception))

    def test_provider_sends_structured_schema_and_preserves_upstream_status(self) -> None:
        fake_client = FakeClient(FakeResponse(400))
        schema = {"type": "object", "properties": {"overview": {"type": "string"}}}

        with (
            patch("app.services.ai_provider.ai_settings", configured_settings(True)),
            patch("app.services.ai_provider.httpx.Client", return_value=fake_client),
            self.assertRaises(AIProviderUpstreamError) as context,
        ):
            OpenAICompatibleProvider().generate("test prompt", response_schema=schema)

        self.assertEqual(context.exception.upstream_status_code, 400)
        self.assertIn("HTTP 400", str(context.exception))
        self.assertIsNotNone(fake_client.payload)
        assert fake_client.payload is not None
        self.assertEqual(fake_client.payload["response_format"]["type"], "json_schema")


if __name__ == "__main__":
    unittest.main()

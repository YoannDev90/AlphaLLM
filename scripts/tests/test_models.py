"""Pytest-compatible test cases for model handlers."""

import os
import sys
import asyncio
import time
import traceback
from unittest.mock import AsyncMock, MagicMock, patch

import litellm
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import cfg
from core.models_loader import Model, get_model_catalog, get_models


class TestModelHandlers:
    """Test cases for model handling."""

    def classify_exception(self, model: Model, exc):
        """Classify exceptions for model testing."""
        msg = str(exc).lower()

        if not model.api_key:
            return "missing_api_key", "No API key set for provider"

        if any(k in msg for k in ("401", "403", "unauthor", "invalid", "api key")):
            return "invalid_api_key", msg

        if any(k in msg for k in ("404", "not found", "model not found")):
            return "model_not_found", msg

        if any(
            k in msg
            for k in (
                "502",
                "503",
                "504",
                "timeout",
                "timed out",
                "connection",
                "failed to establish",
                "name or service not known",
            )
        ):
            return "provider_down", msg

        return "unknown_error", msg

    def summarize_results(self, model, result):
        """Summarize test results."""
        if result["status"] == "ok":
            return ("ok", "Got response", None)
        exc = result.get("exception")
        kind, detail = (
            self.classify_exception(model, exc)
            if exc is not None
            else ("unknown_error", "no exception info")
        )
        return (kind, detail, result.get("trace"))

    def pretty_model_info(self, model):
        """Create a formatted model info string."""
        return f"model={model.litellm_id} provider={model.provider} api_base={model.api_base} api_key_set={bool(model.api_key)}"

    @pytest.mark.asyncio
    async def test_model_availability(self):
        """Test that models are available for testing."""
        models = get_models()
        assert models is not None

        # Should have at least one model available
        assert len(models) > 0, "No models available for testing"

        # Each model should have the required attributes
        for model in models:
            assert isinstance(model, Model)
            assert hasattr(model, "litellm_id")
            assert hasattr(model, "provider")
            assert hasattr(model, "api_base")
            assert hasattr(model, "api_key")

    @pytest.mark.asyncio
    async def test_model_configuration(self):
        """Test that models are properly configured."""
        models = get_models()

        if not models:
            catalog = get_model_catalog()
            # If no models available, at least verify catalog exists
            assert isinstance(catalog, list)
            return

        # Test each model with a simple prompt
        msg = [
            {
                "role": "system",
                "content": "Please answer as concisely as possible; this is just a test",
            },
            {"role": "user", "content": "OK ?"},
        ]

        for model in models:
            model_info = self.pretty_model_info(model)

            # Mock litellm.acompletion to avoid actual API calls
            with patch("litellm.acompletion") as mock_completion:
                mock_completion.return_value = MagicMock(
                    choices=[MagicMock(message=MagicMock(content="Test response"))]
                )

                result = await self._test_model_helper(model, msg, retries=0)

                # Should have attempted to make the call
                mock_completion.assert_called_once()

                # Verify the correct parameters were used
                call_kwargs = mock_completion.call_args[1]
                assert call_kwargs["model"] == model.litellm_id
                assert call_kwargs["api_key"] == model.api_key
                assert call_kwargs["messages"] == msg

                # Verify result structure
                assert "status" in result
                assert "message" in result

    @pytest.mark.asyncio
    async def test_model_error_handling(self):
        """Test error handling for model failures."""
        # Create a mock model that will fail
        mock_model = MagicMock(spec=Model)
        mock_model.litellm_id = "test-model"
        mock_model.provider = "test-provider"
        mock_model.api_base = "https://test.example.com"
        mock_model.api_key = "fake-api-key"

        msg = [
            {"role": "user", "content": "Test error"},
        ]

        # Mock litellm.acompletion to raise an exception
        with patch("litellm.acompletion", side_effect=Exception("Test error")):
            result = await self._test_model_helper(mock_model, msg, retries=0)

            # Should have failed
            assert result["status"] == "error"
            assert "exception" in result

    async def _test_model_helper(self, model: Model, msg, retries=1):
        """Helper method for testing model functionality."""
        last_exc = None
        for attempt in range(1, retries + 2):
            try:
                resp = await litellm.acompletion(
                    model=model.litellm_id,
                    base_url=model.api_base,
                    api_key=model.api_key,
                    messages=msg,
                    timeout=30,
                )
                message = (
                    resp.choices[0].message if getattr(resp, "choices", None) else None
                )
                return {"status": "ok", "message": message, "resp": resp}
            except Exception as e:
                last_exc = e
                # small backoff before retry
                if attempt <= retries:
                    time.sleep(1)
                    continue
                return {
                    "status": "error",
                    "exception": e,
                    "trace": traceback.format_exc(),
                }

    def test_exception_classification_missing_api_key(self):
        """Test exception classification for missing API key."""
        mock_model = MagicMock(spec=Model)
        mock_model.api_key = None

        # Create an exception
        exc = Exception("Test error")
        kind, detail = self.classify_exception(mock_model, exc)

        assert kind == "missing_api_key"

    def test_exception_classification_invalid_api_key(self):
        """Test exception classification for invalid API key."""
        mock_model = MagicMock(spec=Model)
        mock_model.api_key = "fake-key"

        # Test with different error types
        error_cases = [
            Exception("401 Unauthorized"),
            Exception("403 Forbidden"),
            Exception("Invalid API key"),
            Exception("Unauthorized"),
        ]

        for exc in error_cases:
            kind, detail = self.classify_exception(mock_model, exc)
            assert kind == "invalid_api_key"

    def test_exception_classification_model_not_found(self):
        """Test exception classification for model not found."""
        mock_model = MagicMock(spec=Model)
        mock_model.api_key = "fake-key"

        # Test with model not found errors
        error_cases = [
            Exception("404 Not Found"),
            Exception("Model not found"),
        ]

        for exc in error_cases:
            kind, detail = self.classify_exception(mock_model, exc)
            assert kind == "model_not_found"

    def test_exception_classification_provider_down(self):
        """Test exception classification for provider downtime."""
        mock_model = MagicMock(spec=Model)
        mock_model.api_key = "fake-key"

        # Test with provider error cases
        error_cases = [
            Exception("502 Bad Gateway"),
            Exception("503 Service Unavailable"),
            Exception("504 Gateway Timeout"),
            Exception("Connection timeout"),
            Exception("Failed to establish connection"),
            Exception("Name or service not known"),
        ]

        for exc in error_cases:
            kind, detail = self.classify_exception(mock_model, exc)
            assert kind == "provider_down"

    @pytest.mark.asyncio
    async def test_model_retry_logic(self):
        """Test model retry logic."""
        mock_model = MagicMock(spec=Model)
        mock_model.litellm_id = "test-model"
        mock_model.provider = "test-provider"
        mock_model.api_base = "https://test.example.com"
        mock_model.api_key = "fake-api-key"

        msg = [
            {"role": "user", "content": "Test retry"},
        ]

        # Test with retry count
        call_count = 0

        def mock_completion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("First attempt fails")
            return MagicMock(choices=[MagicMock(message=MagicMock(content="Success"))])

        with patch("litellm.acompletion", side_effect=mock_completion):
            result = await self._test_model_helper(mock_model, msg, retries=1)

            # Should have retried
            assert call_count == 2
            assert result["status"] == "ok"

    def test_pretty_model_info_format(self):
        """Test pretty model info formatting."""
        mock_model = MagicMock(spec=Model)
        mock_model.litellm_id = "gpt-4"
        mock_model.provider = "openai"
        mock_model.api_base = "https://api.openai.com/v1"
        mock_model.api_key = "sk-test-key"

        info = self.pretty_model_info(mock_model)

        assert "model=gpt-4" in info
        assert "provider=openai" in info
        assert "api_base=https://api.openai.com/v1" in info
        assert "api_key_set=True" in info

        # Test with None API key
        mock_model.api_key = None
        info = self.pretty_model_info(mock_model)
        assert "api_key_set=False" in info


# Additional standalone test functions using fixtures
@pytest.fixture
def mock_model():
    """Fixture providing a mock model for testing."""
    mock_model = MagicMock(spec=Model)
    mock_model.litellm_id = "test-model"
    mock_model.provider = "test-provider"
    mock_model.api_base = "https://test.example.com"
    mock_model.api_key = "fake-api-key"
    return mock_model


@pytest.fixture
def test_message():
    """Fixture providing test message."""
    return [
        {"role": "user", "content": "Test message"},
    ]


# Standalone test function using the mock model fixture
@pytest.mark.asyncio
async def test_model_with_mock_fixture(mock_model, test_message):
    """Test model using pytest fixtures."""
    # Mock litellm.acompletion to avoid actual API calls
    with patch("litellm.acompletion") as mock_completion:
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test response"))]
        )

        handler = TestModelHandlers()
        result = await handler._test_model_helper(mock_model, test_message, retries=0)

        # Should have attempted to make the call
        mock_completion.assert_called_once()
        assert "status" in result
        assert "message" in result

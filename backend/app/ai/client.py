"""
DietSense — Google Gemini Client Manager
Wraps the google-genai SDK with async execution, client-side rate limiting,
hash-based caching, timeout enforcement, and clinical audit logging.
"""

import time
import uuid
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

from app.core.config import settings
from app.ai.rate_limiter import global_rate_limiter, user_rate_limiter, ai_response_cache
from db.database import get_db_cursor

logger = logging.getLogger("dietsense.ai")


class GeminiClientManager:
    """Manages Gemini API lifecycle, async execution, rate limiting, and fallback."""

    def __init__(self):
        self._client = None
        self._initialized = False
        self._init_error = None

    def _get_client(self):
        """Lazy-initializes google-genai Client."""
        if not self._initialized:
            api_key = (settings.gemini_api_key or "").strip()
            if not api_key or "your-gemini-api-key" in api_key.lower():
                self._client = None
                self._init_error = "API key not configured"
            else:
                try:
                    from google import genai
                    self._client = genai.Client(api_key=api_key)
                    self._init_error = None
                except Exception as e:
                    self._client = None
                    self._init_error = str(e)
                    logger.warning("Failed to initialize google-genai Client: %s", e)
            self._initialized = True
        return self._client

    @property
    def is_available(self) -> bool:
        """Returns True if Gemini API key is configured and AI is enabled."""
        if not settings.ai_feature_enabled:
            return False
        return self._get_client() is not None

    def log_interaction(
        self,
        user_id: str,
        feature: str,
        model: str,
        latency_ms: int,
        status: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """Persists audit record to SQLite ai_interaction_logs table."""
        try:
            with get_db_cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO ai_interaction_logs (
                        id, user_id, feature, model, prompt_tokens, completion_tokens,
                        total_tokens, latency_ms, status, error_message, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"ai_log_{uuid.uuid4().hex[:16]}",
                        user_id or "anonymous",
                        feature,
                        model,
                        prompt_tokens,
                        completion_tokens,
                        prompt_tokens + completion_tokens,
                        latency_ms,
                        status,
                        error_message[:255] if error_message else None,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
        except Exception as e:
            # Audit log failure should never crash the main application
            logger.debug("Could not record ai_interaction_logs: %s", e)

    async def generate_text(
        self,
        prompt: str,
        user_id: str = "anonymous",
        feature: str = "assistant",
        system_instruction: Optional[str] = None,
        response_schema: Optional[Any] = None,
        cache_key_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[str], str]:
        """
        Executes an asynchronous generation call against Gemini.
        Returns (result_text, status_code).
        Status codes: 'success', 'cached', 'rate_limited', 'offline', 'timeout', 'error'.
        """
        # 1. Check feature flag and client readiness
        if not settings.ai_feature_enabled or not self.is_available:
            return None, "offline"

        # 2. Check Cache
        cache_key = None
        if cache_key_data:
            cache_key = ai_response_cache.generate_key(feature, cache_key_data)
            cached_val = ai_response_cache.get(cache_key)
            if cached_val is not None:
                return cached_val, "cached"

        # 3. Check Rate Limits (User & Global)
        user_allowed, _ = user_rate_limiter.is_allowed(user_id)
        global_allowed, _ = global_rate_limiter.is_allowed("global")
        if not user_allowed or not global_allowed:
            self.log_interaction(
                user_id=user_id,
                feature=feature,
                model=settings.gemini_model,
                latency_ms=0,
                status="fallback_ratelimit",
                error_message="Rate limit threshold exceeded",
            )
            return None, "rate_limited"

        # 4. Invoke Gemini with Timeout
        client = self._get_client()
        start_time = time.time()
        timeout = settings.gemini_request_timeout

        models_to_try = [settings.gemini_model]
        if settings.gemini_fallback_model and settings.gemini_fallback_model != settings.gemini_model:
            models_to_try.append(settings.gemini_fallback_model)

        last_error = None
        for current_model in models_to_try:
            try:
                try:
                    from google.genai import types
                    config_args = {}
                    if system_instruction:
                        config_args["system_instruction"] = system_instruction
                    if response_schema:
                        config_args["response_mime_type"] = "application/json"
                        config_args["response_schema"] = response_schema
                    config = types.GenerateContentConfig(**config_args) if config_args else None
                except (ImportError, ModuleNotFoundError):
                    config = None

                coro = client.aio.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=config,
                )

                response = await asyncio.wait_for(coro, timeout=timeout)
                latency_ms = int((time.time() - start_time) * 1000)

                result_text = getattr(response, "text", None)
                if not result_text:
                    continue

                prompt_tokens = getattr(getattr(response, "usage_metadata", None), "prompt_token_count", 0) or 0
                candidate_tokens = getattr(getattr(response, "usage_metadata", None), "candidates_token_count", 0) or 0

                self.log_interaction(
                    user_id=user_id,
                    feature=feature,
                    model=current_model,
                    latency_ms=latency_ms,
                    status="success",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=candidate_tokens,
                )

                if cache_key:
                    ai_response_cache.set(cache_key, result_text)

                return result_text, "success"

            except asyncio.TimeoutError:
                last_error = f"Timed out on {current_model}"
                logger.warning("Gemini model %s timed out after %ss", current_model, timeout)
            except Exception as e:
                last_error = str(e)
                logger.warning("Gemini model %s error: %s", current_model, e)

        latency_ms = int((time.time() - start_time) * 1000)
        self.log_interaction(
            user_id=user_id,
            feature=feature,
            model=settings.gemini_model,
            latency_ms=latency_ms,
            status="fallback_error",
            error_message=last_error or "All models failed",
        )
        return None, "error"


# Singleton instance
gemini_client = GeminiClientManager()

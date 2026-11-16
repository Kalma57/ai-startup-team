"""Gemini call wrapper: retry on rate limits / overload with exponential backoff."""
import logging
import random
import time
from typing import Callable, TypeVar

from google.genai import errors

log = logging.getLogger("llm")

T = TypeVar("T")
RETRYABLE_CODES = {429, 503}
MAX_ATTEMPTS = 4
BASE_DELAY_SECONDS = 2.0


def call_with_retry(fn: Callable[[], T], what: str,
                    sleep: Callable[[float], None] = time.sleep) -> T:
    """Run ``fn``; retry on HTTP 429/503 (free-tier limits are low).

    Any other API error is raised immediately - retrying will not fix it.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return fn()
        except errors.APIError as exc:
            retryable = exc.code in RETRYABLE_CODES
            if not retryable or attempt == MAX_ATTEMPTS:
                log.error("%s failed (HTTP %s) after %d attempt(s): %s",
                          what, exc.code, attempt, exc.message)
                raise
            delay = BASE_DELAY_SECONDS * (2 ** (attempt - 1)) + random.uniform(0, 1)
            log.warning("%s hit HTTP %s (attempt %d/%d), retrying in %.1fs",
                        what, exc.code, attempt, MAX_ATTEMPTS, delay)
            sleep(delay)
    raise RuntimeError("unreachable")  # pragma: no cover

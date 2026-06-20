from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
import time
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


logger = logging.getLogger("dsa_agent.llm")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


class LlmClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response from an LLM provider."""


class MissingApiKeyError(RuntimeError):
    """Raised when the project is configured for LLM-only mode without a key."""


class TransientLlmError(RuntimeError):
    """Raised when the LLM provider is temporarily unavailable after retries."""


@dataclass
class OpenRouterLlmClient:
    """OpenRouter REST API client for tutor-facing generation."""

    api_key: str
    model: str = "google/gemini-2.5-flash"
    timeout_seconds: int = 60
    max_retries: int = 2

    @classmethod
    def from_env(cls, model: str = "google/gemini-2.5-flash") -> "OpenRouterLlmClient":
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key or api_key == "paste-your-openrouter-api-key-here":
            raise MissingApiKeyError(
                "OPENROUTER_API_KEY is required. Put it in .env or an environment variable."
            )

        return cls(api_key=api_key, model=model)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = "https://openrouter.ai/api/v1/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": 0.4,
        }

        logger.info(
            "[OpenRouter] preparing request | model=%s | system_chars=%d | user_chars=%d",
            self.model,
            len(system_prompt),
            len(user_prompt),
        )

        # Không log API key. Chỉ log preview ngắn để biết request đã được tạo.
        logger.info(
            "[OpenRouter] request preview | user_prompt_preview=%r",
            user_prompt[:250],
        )

        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        raw = self._send_with_retries(request)

        logger.info(
            "[OpenRouter] raw response received | chars=%d | preview=%r",
            len(raw),
            raw[:500],
        )

        body = json.loads(raw)
        try:
            message = body["choices"][0]["message"]
            content = message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.exception("[OpenRouter] unexpected response shape")
            raise RuntimeError(f"Unexpected OpenRouter response: {body}") from exc

        text = self._normalize_content(content)
        if not text:
            logger.error("[OpenRouter] empty response | body=%s", body)
            raise RuntimeError(f"OpenRouter returned an empty response: {body}")

        logger.info(
            "[OpenRouter] generated text | chars=%d | preview=%r",
            len(text),
            text[:500],
        )

        return text

    def _send_with_retries(self, request: Request) -> str:
        transient_codes = {408, 409, 425, 429, 500, 502, 503, 504}
        last_error = ""

        for attempt in range(self.max_retries + 1):
            logger.info(
                "[OpenRouter] sending request | attempt=%d/%d",
                attempt + 1,
                self.max_retries + 1,
            )

            started_at = time.perf_counter()

            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    raw = response.read().decode("utf-8")
                    elapsed = time.perf_counter() - started_at

                    logger.info(
                        "[OpenRouter] response arrived | status=%s | elapsed=%.2fs | chars=%d",
                        getattr(response, "status", "unknown"),
                        elapsed,
                        len(raw),
                    )

                    return raw

            except HTTPError as exc:
                elapsed = time.perf_counter() - started_at
                details = exc.read().decode("utf-8", errors="replace")
                last_error = self._extract_error_message(details) or f"HTTP {exc.code}"

                logger.warning(
                    "[OpenRouter] HTTP error | status=%s | elapsed=%.2fs | message=%s | details_preview=%r",
                    exc.code,
                    elapsed,
                    last_error,
                    details[:500],
                )

                if exc.code not in transient_codes or attempt >= self.max_retries:
                    if exc.code in transient_codes:
                        raise TransientLlmError(
                            f"OpenRouter đang quá tải hoặc tạm thời không khả dụng ({exc.code}). "
                            "Hãy thử gửi lại sau ít phút."
                        ) from exc

                    raise RuntimeError(f"OpenRouter API error {exc.code}: {last_error}") from exc

                sleep_seconds = 0.8 * (attempt + 1)
                logger.info("[OpenRouter] retrying after %.1fs", sleep_seconds)
                time.sleep(sleep_seconds)

            except URLError as exc:
                elapsed = time.perf_counter() - started_at
                last_error = str(exc.reason)

                logger.warning(
                    "[OpenRouter] connection error | elapsed=%.2fs | reason=%s",
                    elapsed,
                    last_error,
                )

                if attempt >= self.max_retries:
                    raise TransientLlmError(
                        "Không kết nối được tới OpenRouter API. Hãy kiểm tra mạng rồi thử lại."
                    ) from exc

                sleep_seconds = 0.8 * (attempt + 1)
                logger.info("[OpenRouter] retrying after %.1fs", sleep_seconds)
                time.sleep(sleep_seconds)

        raise TransientLlmError(last_error or "OpenRouter tạm thời không khả dụng.")

    @staticmethod
    def _normalize_content(content: object) -> str:
        """
        OpenRouter thường trả content dạng string.
        Một số model/provider có thể trả content dạng list part.
        """
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text") or part.get("content")
                    if isinstance(text, str):
                        parts.append(text)
                elif isinstance(part, str):
                    parts.append(part)

            return "".join(parts).strip()

        return str(content).strip() if content is not None else ""

    @staticmethod
    def _extract_error_message(details: str) -> str:
        try:
            body = json.loads(details)
        except json.JSONDecodeError:
            return details.strip()

        error = body.get("error", {})
        if isinstance(error, dict):
            return str(error.get("message", "")).strip()

        if isinstance(error, str):
            return error.strip()

        return details.strip()


# Giữ alias để code cũ vẫn chạy:
# from dsa_agent.llm_client import GeminiLlmClient
GeminiLlmClient = OpenRouterLlmClient
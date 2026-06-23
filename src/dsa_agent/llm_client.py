from __future__ import annotations

from dataclasses import dataclass
import json
import os
import time
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LlmClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response from an LLM provider."""


class MissingApiKeyError(RuntimeError):
    """Raised when the project is configured for LLM-only mode without a key."""


class TransientLlmError(RuntimeError):
    """Raised when the LLM provider is temporarily unavailable after retries."""


@dataclass
class GeminiLlmClient:
    """Gemini REST API client for tutor-facing generation."""

    api_key: str
    model: str = "gemini-flash-latest"
    timeout_seconds: int = 60
    max_retries: int = 2

    @classmethod
    def from_env(cls, model: str = "gemini-flash-latest") -> "GeminiLlmClient":
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key or api_key == "paste-your-gemini-api-key-here":
            raise MissingApiKeyError("GEMINI_API_KEY is required. Put it in .env or an environment variable.")
        return cls(api_key=api_key, model=model)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
        }
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": self.api_key,
            },
        )

        raw = self._send_with_retries(request)

        body = json.loads(raw)
        try:
            parts = body["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected Gemini response: {body}") from exc

        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise RuntimeError(f"Gemini returned an empty response: {body}")
        return text

    def _send_with_retries(self, request: Request) -> str:
        transient_codes = {429, 500, 502, 503, 504}
        last_error = ""

        for attempt in range(self.max_retries + 1):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    return response.read().decode("utf-8")
            except HTTPError as exc:
                details = exc.read().decode("utf-8", errors="replace")
                last_error = self._extract_error_message(details) or f"HTTP {exc.code}"
                if exc.code not in transient_codes or attempt >= self.max_retries:
                    if exc.code in transient_codes:
                        raise TransientLlmError(
                            f"Gemini đang quá tải hoặc tạm thời không khả dụng ({exc.code}). Hãy thử gửi lại sau ít phút."
                        ) from exc
                    raise RuntimeError(f"Gemini API error {exc.code}: {last_error}") from exc
                time.sleep(0.8 * (attempt + 1))
            except URLError as exc:
                last_error = str(exc.reason)
                if attempt >= self.max_retries:
                    raise TransientLlmError("Không kết nối được tới Gemini API. Hãy kiểm tra mạng rồi thử lại.") from exc
                time.sleep(0.8 * (attempt + 1))

        raise TransientLlmError(last_error or "Gemini tạm thời không khả dụng.")

    @staticmethod
    def _extract_error_message(details: str) -> str:
        try:
            body = json.loads(details)
        except json.JSONDecodeError:
            return details.strip()
        error = body.get("error", {})
        if isinstance(error, dict):
            return str(error.get("message", "")).strip()
        return details.strip()

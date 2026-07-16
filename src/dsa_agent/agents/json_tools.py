from __future__ import annotations

import json


def loads_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()

    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("Expected LLM to return a JSON object.")
    return data

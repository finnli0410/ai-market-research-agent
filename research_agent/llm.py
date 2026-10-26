"""Minimal OpenAI-compatible chat client. Configure with env vars:
RESEARCH_LLM_API_KEY, RESEARCH_LLM_BASE_URL (default https://api.openai.com/v1), RESEARCH_LLM_MODEL."""
from __future__ import annotations

import json
import os
import re

import requests


class LLMNotConfigured(RuntimeError):
    pass


def configured() -> bool:
    return bool(os.getenv("RESEARCH_LLM_API_KEY"))


def chat_json(system: str, user: str, timeout: float = 120) -> dict:
    key = os.getenv("RESEARCH_LLM_API_KEY")
    if not key:
        raise LLMNotConfigured("Set RESEARCH_LLM_API_KEY or use --demo")
    base = os.getenv("RESEARCH_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("RESEARCH_LLM_MODEL", "gpt-4o-mini")
    r = requests.post(f"{base}/chat/completions", timeout=timeout,
                      headers={"Authorization": f"Bearer {key}"},
                      json={"model": model, "temperature": 0.2,
                            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
    r.raise_for_status()
    return parse_json(r.json()["choices"][0]["message"]["content"])


def parse_json(content: str) -> dict:
    """Accept raw JSON or JSON wrapped in a ```json fence."""
    m = re.search(r"```(?:json)?\s*(.*?)```", content, re.S)
    return json.loads(m.group(1) if m else content)

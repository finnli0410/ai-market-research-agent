"""Web search (DuckDuckGo HTML endpoint, no key) and page reading."""
from __future__ import annotations

import html
import re
from urllib.parse import parse_qs, unquote, urlparse

import requests

UA = {"User-Agent": "Mozilla/5.0 (research-agent; +https://github.com/finnli0410/ai-market-research-agent)"}
_RESULT = re.compile(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S)
_TAG = re.compile(r"<[^>]+>")


def _clean_url(href: str) -> str:
    if "uddg=" in href:
        return unquote(parse_qs(urlparse(href).query)["uddg"][0])
    return href


def parse_results(page: str, limit: int) -> list[tuple[str, str]]:
    out = []
    for href, title in _RESULT.findall(page):
        out.append((html.unescape(_TAG.sub("", title)).strip(), _clean_url(html.unescape(href))))
        if len(out) >= limit:
            break
    return out


def search(query: str, limit: int = 6, timeout: float = 15) -> list[tuple[str, str]]:
    r = requests.post("https://html.duckduckgo.com/html/", data={"q": query}, headers=UA, timeout=timeout)
    r.raise_for_status()
    return parse_results(r.text, limit)


def extract_text(page: str, max_chars: int = 6000) -> str:
    page = re.sub(r"(?is)<(script|style|nav|footer|header).*?</\1>", " ", page)
    text = html.unescape(_TAG.sub(" ", page))
    return re.sub(r"\s+", " ", text).strip()[:max_chars]


def read(url: str, timeout: float = 15) -> str:
    try:
        r = requests.get(url, headers=UA, timeout=timeout)
        r.raise_for_status()
        return extract_text(r.text)
    except requests.RequestException:
        return ""

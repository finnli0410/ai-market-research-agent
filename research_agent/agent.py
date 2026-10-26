from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from . import llm, search
from .models import FORCES, Report, Source
from .strategy import RULES

SAMPLES = Path(__file__).resolve().parent.parent / "samples"

SYSTEM = f"""You are a strategy analyst. Using ONLY the numbered sources provided, return JSON:
{{"summary": {{"claim": str, "sources": [int]}},
 "competitors": [{{"name": str, "positioning": str, "sources": [int]}}],
 "five_forces": {{{", ".join(f'"{f}"' for f in FORCES)}: {{"rating": "low|medium|high", "rationale": str, "sources": [int]}}}},
 "key_success_factors": [{{"claim": str, "sources": [int]}}],
 "risks": [{{"claim": str, "sources": [int]}}],
 "indicators": [{{"name": one of {sorted({k for r in RULES.values() for k in r})}, "value": number or "low|medium|high|worse|similar|better", "force": str, "sources": [int]}}]}}
Only report an indicator whose value appears in a source.
Every claim must cite at least one source id. If the sources do not support a field, say "insufficient evidence" with sources []. Never invent numbers."""

QUERIES = ["{s} market size", "{s} competitors", "{s} funding revenue ARR", "{s} regulation risks"]


def gather(subject: str, per_query: int = 3, searcher: Callable = search.search, reader: Callable = search.read) -> list[Source]:
    seen, sources = set(), []
    for q in QUERIES:
        for title, url in searcher(q.format(s=subject), per_query):
            if url in seen:
                continue
            seen.add(url)
            text = reader(url)
            if text:
                sources.append(Source(len(sources) + 1, title, url, text))
    return sources


def run(subject: str, demo: bool = False, sample: str = "french_accounting_saas") -> Report:
    if demo or not llm.configured():
        d = json.loads((SAMPLES / f"{sample}.json").read_text())
        return Report.from_dict(d["subject"], d["report"], [Source(**s) for s in d["sources"]])
    sources = gather(subject)
    if not sources:
        raise RuntimeError("No readable sources found")
    ctx = "\n\n".join(f"[{s.id}] {s.title} ({s.url})\n{s.text}" for s in sources)
    report = Report.from_dict(subject, llm.chat_json(SYSTEM, f"Subject: {subject}\n\nSources:\n{ctx}"), sources)
    bad = report.cited_ids() - {s.id for s in sources}
    if bad:
        raise ValueError(f"Report cites unknown source ids: {sorted(bad)}")
    return report

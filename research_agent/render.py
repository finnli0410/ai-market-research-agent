from __future__ import annotations

from .models import FORCES, Report
from .strategy import Indicator, score_force

LABEL = {"rivalry": "Competitive rivalry", "new_entrants": "Threat of new entrants", "buyer_power": "Buyer power",
         "supplier_power": "Supplier power", "substitutes": "Threat of substitutes"}


def _cite(ids: list[int]) -> str:
    return " " + "".join(f"[{i}]" for i in ids) if ids else ""


def to_markdown(r: Report) -> str:
    L = [f"# Market research: {r.subject}", "", f"**Bottom line:** {r.summary.claim}{_cite(r.summary.sources)}", "",
         "## Competitors", "| Company | Positioning | Sources |", "|---|---|---|"]
    L += [f"| {c['name']} | {c['positioning']} |{_cite(c.get('sources', []))} |" for c in r.competitors]
    L += ["", "## Five forces", "| Force | Rating | Rationale |", "|---|---|---|"]
    for f in FORCES:
        x = r.five_forces.get(f, {"rating": "n/a", "rationale": "insufficient evidence", "sources": []})
        L.append(f"| {LABEL[f]} | {x['rating']} | {x['rationale']}{_cite(x.get('sources', []))} |")
    if r.indicators:
        L += ["", "### Quantified force scores (1 = weak force, 5 = strong; rules in `strategy.py`)",
              "| Force | Score | Rating | Indicators |", "|---|---|---|---|"]
        for f in FORCES:
            inds = [Indicator(i["name"], i["value"], tuple(i.get("sources", []))) for i in r.indicators if i.get("force") == f]
            fs = score_force(f, inds)
            ev = "; ".join(f"{i.name}={i.value} → {s}{_cite(list(i.sources))}" for i, s in fs.evidence) or "none sourced"
            L.append(f"| {LABEL[f]} | {fs.score if fs.score is not None else '-'} | {fs.rating} | {ev} |")
    L += ["", "## Key success factors"] + [f"- {p.claim}{_cite(p.sources)}" for p in r.key_success_factors]
    L += ["", "## Risks"] + [f"- {p.claim}{_cite(p.sources)}" for p in r.risks]
    L += ["", "## Sources"] + [f"{s.id}. [{s.title}]({s.url})" for s in r.sources]
    return "\n".join(L) + "\n"

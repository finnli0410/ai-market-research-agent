from __future__ import annotations

from dataclasses import dataclass, field

FORCES = ("rivalry", "new_entrants", "buyer_power", "supplier_power", "substitutes")


@dataclass
class Source:
    id: int
    title: str
    url: str
    text: str = ""


@dataclass
class Point:
    claim: str
    sources: list[int] = field(default_factory=list)


@dataclass
class Report:
    subject: str
    summary: Point
    competitors: list[dict]                 # {name, positioning, sources}
    five_forces: dict[str, dict]            # force -> {rating, rationale, sources}
    key_success_factors: list[Point]
    risks: list[Point]
    sources: list[Source]
    indicators: list[dict] = field(default_factory=list)   # {name, value, sources}

    @classmethod
    def from_dict(cls, subject: str, d: dict, sources: list[Source]) -> "Report":
        pt = lambda x: Point(x["claim"], list(x.get("sources", [])))
        missing = [k for k in ("summary", "competitors", "five_forces", "key_success_factors", "risks") if k not in d]
        if missing:
            raise ValueError(f"LLM output missing keys: {missing}")
        return cls(subject, pt(d["summary"]), d["competitors"], d["five_forces"],
                   [pt(x) for x in d["key_success_factors"]], [pt(x) for x in d["risks"]], sources,
                   list(d.get("indicators", [])))

    def cited_ids(self) -> set[int]:
        ids = set(self.summary.sources)
        for c in self.competitors: ids |= set(c.get("sources", []))
        for f in self.five_forces.values(): ids |= set(f.get("sources", []))
        for p in self.key_success_factors + self.risks: ids |= set(p.sources)
        for i in self.indicators: ids |= set(i.get("sources", []))
        return ids

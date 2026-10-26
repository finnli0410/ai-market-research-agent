"""Strategic analysis engine: quantified five forces, VRIO and value capture.

Every score is derived from an Indicator that carries a value and a source id.
Missing indicators yield 'insufficient evidence', never a default guess."""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Literal

Level = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class Indicator:
    name: str
    value: float | str
    sources: tuple[int, ...]
    unit: str = ""


# ---------------------------------------------------------------- concentration
def hhi(shares_pct: list[float]) -> float:
    """Herfindahl-Hirschman index on percentage shares (0-10,000).
    With only the top-k shares known, this is a lower bound (the residual's split is unknown)."""
    if any(s < 0 for s in shares_pct) or sum(shares_pct) > 100.0001:
        raise ValueError("shares must be non-negative and sum to <= 100")
    return float(sum(s * s for s in shares_pct))


def hhi_band(h: float) -> str:
    """US DOJ/FTC Merger Guidelines (2023): > 1,800 highly concentrated; 1,000-1,800 moderately."""
    return "highly concentrated" if h > 1800 else "moderately concentrated" if h >= 1000 else "unconcentrated"


def cr(shares_pct: list[float], k: int = 4) -> float:
    return float(sum(sorted(shares_pct, reverse=True)[:k]))


# ---------------------------------------------------------------- five forces
# Each rule maps one measurable indicator to a 1 (weak force) .. 5 (strong force) score.
def _band(x: float, cuts: tuple[float, float, float, float], reverse: bool = False) -> int:
    s = 1 + sum(x > c for c in cuts)
    return 6 - s if reverse else s


RULES = {
    # rivalry is weaker when the market is concentrated and growing
    "rivalry": {"hhi": lambda v: _band(v, (1000, 1800, 3000, 5000), reverse=True),
                "market_growth_pct": lambda v: _band(v, (0, 5, 10, 20), reverse=True)},
    # new entrants are deterred by capital intensity and switching costs
    "new_entrants": {"capex_to_revenue_pct": lambda v: _band(v, (5, 10, 20, 30), reverse=True),
                     "switching_costs": lambda v: {"low": 5, "medium": 3, "high": 1}[v]},
    "buyer_power": {"top_customer_share_pct": lambda v: _band(v, (5, 10, 20, 30)),
                    "switching_costs": lambda v: {"low": 5, "medium": 3, "high": 1}[v]},
    "supplier_power": {"supplier_hhi": lambda v: _band(v, (1000, 1800, 3000, 5000))},
    "substitutes": {"substitute_price_performance": lambda v: {"worse": 1, "similar": 3, "better": 5}[v]},
}


@dataclass
class ForceScore:
    force: str
    score: float | None           # 1..5, None if no evidence
    rating: str
    evidence: list[tuple[Indicator, int]] = field(default_factory=list)

    @property
    def sources(self) -> list[int]:
        return sorted({s for ind, _ in self.evidence for s in ind.sources})


def score_force(force: str, indicators: list[Indicator]) -> ForceScore:
    rules = RULES[force]
    ev = [(i, rules[i.name](i.value)) for i in indicators if i.name in rules]
    if not ev:
        return ForceScore(force, None, "insufficient evidence")
    s = mean(x for _, x in ev)
    return ForceScore(force, round(s, 2), "low" if s < 2.5 else "medium" if s < 3.5 else "high", ev)


def industry_attractiveness(scores: list[ForceScore]) -> float | None:
    """1 (unattractive) .. 5 (attractive) = 6 - mean force strength over forces with evidence."""
    known = [f.score for f in scores if f.score is not None]
    return round(6 - mean(known), 2) if known else None


# ---------------------------------------------------------------- VRIO
@dataclass(frozen=True)
class Evidence:
    passed: bool
    evidence: str
    sources: tuple[int, ...]


def vrio(valuable: Evidence, rare: Evidence, inimitable: Evidence, organized: Evidence) -> str:
    """Barney (1991; Barney & Hesterly) VRIO implication, evaluated in order. Each test needs a cited source."""
    for t in (valuable, rare, inimitable, organized):
        if not t.sources:
            raise ValueError("every VRIO test needs at least one source")
    if not valuable.passed:
        return "competitive disadvantage"
    if not rare.passed:
        return "competitive parity"
    if not inimitable.passed:
        return "temporary competitive advantage"
    if not organized.passed:
        return "unexploited competitive advantage"
    return "sustained competitive advantage"


# ---------------------------------------------------------------- value creation / capture
@dataclass(frozen=True)
class ValueSplit:
    created: float        # WTP - cost
    firm: float           # price - cost
    buyer: float          # WTP - price
    firm_share: float     # firm / created


def value_split(wtp: float, price: float, cost: float) -> ValueSplit:
    """Brandenburger & Stuart (1996) value-based strategy, per unit."""
    if not cost <= price <= wtp:
        raise ValueError("requires cost <= price <= willingness to pay")
    created = wtp - cost
    return ValueSplit(created, price - cost, wtp - price, (price - cost) / created if created else 0.0)


def gross_margin_capture(revenue: float, cogs: float) -> float:
    """Observable lower-bound proxy for value captured by the firm: (price - cost) / price."""
    return (revenue - cogs) / revenue

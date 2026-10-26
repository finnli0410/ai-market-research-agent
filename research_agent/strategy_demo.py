"""Worked example of the strategy engine on the foundry market (all inputs cited).
python -m research_agent.strategy_demo > samples/foundry_strategy.md"""
from __future__ import annotations

from .strategy import (Indicator, Evidence, cr, gross_margin_capture, hhi, hhi_band, industry_attractiveness,
                       score_force, vrio)

SOURCES = {
    1: ("TrendForce, 2Q25 top-10 foundry ranking", "https://www.trendforce.com/presscenter/news/20250901-12691.html"),
    2: ("TSMC 4Q25 Management Report", "https://investor.tsmc.com/english/encrypt/files/encrypt_file/reports/2026-01/00fe50f72b38d74e6b9b066398f020f337cd4e9d/4Q25%20Management%20Report.pdf"),
    3: ("TSMC 4Q25 earnings-call transcript", "https://investor.tsmc.com/english/encrypt/files/encrypt_file/reports/2026-01/51d09df96cd89ac19d65af39032b038dc2896a24/TSMC%204Q25%20Transcript.pdf"),
    4: ("TSMC 2014 Annual Report, Company Profile", "https://investor.tsmc.com/static/annualReports/2014/english/e_2_2.html"),
}
SHARES = {"TSMC": 70.2, "Samsung": 7.3, "SMIC": 5.1, "UMC": 4.4, "GlobalFoundries": 3.9,
          "Huahong": 2.5, "VIS": 0.9, "Tower": 0.9, "Nexchip": 0.8, "PSMC": 0.8}   # [1]
REVENUE_2025, CAPEX_2025, GM_2025 = 122.42, 40.90, 0.599                       # US$bn [2][3]; GM [2]


def main() -> None:
    h = hhi(list(SHARES.values()))
    capex_int = CAPEX_2025 / REVENUE_2025 * 100
    forces = [
        score_force("rivalry", [Indicator("hhi", h, (1,))]),
        score_force("new_entrants", [Indicator("capex_to_revenue_pct", capex_int, (2, 3), "%")]),
        score_force("buyer_power", []),
        score_force("supplier_power", []),
        score_force("substitutes", []),
    ]
    v = vrio(Evidence(True, f"gross margin {GM_2025:.1%} (2025)", (2,)),
             Evidence(True, f"{SHARES['TSMC']}% foundry share vs {SHARES['Samsung']}% for No. 2", (1,)),
             Evidence(True, f"capex US${CAPEX_2025}bn in 2025 ({capex_int:.0f}% of revenue)", (2, 3)),
             Evidence(True, "pure-play model: 'never compete with our customers'", (4,)))
    print("# Foundry market: quantified strategic analysis\n")
    print(f"- **Concentration:** HHI (top-10 shares) = **{h:,.0f}**, a lower bound → {hhi_band(h)}; CR4 = {cr(list(SHARES.values())):.1f}% [1]")
    print(f"- **Capital intensity:** capex / revenue 2025 = {CAPEX_2025}/{REVENUE_2025} = **{capex_int:.1f}%** [2][3]")
    print(f"- **Value captured (gross-margin proxy):** {gross_margin_capture(1, 1 - GM_2025):.1%} of TSMC revenue [2]\n")
    print("| Force | Score (1-5) | Rating | Indicators |\n|---|---|---|---|")
    for f in forces:
        ind = "; ".join(f"{i.name}={i.value:,.1f} → {s}" if isinstance(i.value, float) else f"{i.name}={i.value} → {s}"
                        for i, s in f.evidence) or "none sourced"
        cite = "".join(f"[{s}]" for s in f.sources)
        print(f"| {f.force} | {f.score if f.score is not None else '-'} | {f.rating} | {ind} {cite} |")
    print(f"\n**Attractiveness (forces with evidence only):** {industry_attractiveness(forces)} / 5\n")
    print(f"**VRIO, leading-edge manufacturing at scale:** {v} [1][2][3][4]\n")
    print("## Sources")
    for k, (t, u) in SOURCES.items():
        print(f"{k}. [{t}]({u})")


if __name__ == "__main__":
    main()

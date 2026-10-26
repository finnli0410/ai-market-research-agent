# Design notes

## Key decisions
- **The LLM extracts and the code scores.** The model returns indicators with source ids, and `strategy.py` turns them into scores with fixed, tested rules. Scores are reproducible and auditable, while model judgement is limited to reading sources.
- **No evidence, no score.** A force without a sourced indicator is reported as "insufficient evidence" and left out of the attractiveness average.
- **Citation integrity is enforced.** A report citing an unknown source id fails the run.
- **The provider is an OpenAI-compatible endpoint set through env vars,** so there is no vendor lock-in.

## Frameworks: operationalisation and limits
| Framework | Operationalised as | Where it breaks |
|---|---|---|
| Five forces (Porter, 1979, *HBR* 57(2); 2008, *HBR* 86(1)) | Rivalry: HHI and market growth. Entry: capex/revenue and switching costs. Buyers: top-customer share and switching costs. Suppliers: supplier HHI. Substitutes: relative price-performance | Static, at the industry level. It misses complementors (Brandenburger & Nalebuff, 1996) and platform or network effects, and the cut-offs are heuristics, not estimated parameters |
| Concentration (DOJ/FTC *Merger Guidelines*, 2023) | HHI on revenue shares. Top-k only gives a lower bound | Depends on how the market is defined. A global HHI hides segment-level concentration (e.g. leading-edge nodes) |
| VRIO (Barney, 1991, *J. of Management* 17(1); Barney & Hesterly) | Four ordered tests, each with cited evidence | Binary tests on a continuous reality. "Inimitable" is inferred from proxies (cumulative capex), not observed |
| Value-based strategy (Brandenburger & Stuart, 1996, *JEMS* 5(1)) | `value_split` per unit; gross margin as an observable proxy for value captured | Willingness to pay is rarely observable, so the gross-margin proxy ignores buyer surplus |
| Dynamic capabilities (Teece, Pisano & Shuen, 1997, *SMJ* 18(7)) | Not scored | No measurable indicator is robust enough. It is left to qualitative risks rather than a made-up score |

## Alternatives rejected
- **Letting the LLM rate forces directly:** fast, but not reproducible, and the ratings drift with the prompt.
- **Agent frameworks (LangChain etc.):** they hide the prompt and the control flow for a 4-step pipeline.
- **A paid search API:** it would add a second key. DuckDuckGo's HTML endpoint keeps the tool runnable by anyone.

## Issues handled
- DuckDuckGo returns redirect links (`/l/?uddg=`), so `_clean_url` unwraps them (tested).
- Models often wrap JSON in fences, so `parse_json` accepts both forms.
- pytest tried to collect the dataclass `Test` as a test class, so it was renamed `Evidence`.
- The CLI left a file handle open, which raised a ResourceWarning. It now uses a context manager, and the suite runs with `-W error`.

## Known limitations
- No entailment check between a claim and its source.
- Indicator cut-offs are global. Industry-specific calibration is not implemented.

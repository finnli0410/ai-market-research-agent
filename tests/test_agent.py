import json

import pytest

from research_agent import agent, llm
from research_agent.__main__ import main
from research_agent.models import Report, Source
from research_agent.render import to_markdown
from research_agent.search import extract_text, parse_results


def test_demo_runs_without_key(monkeypatch):
    monkeypatch.delenv("RESEARCH_LLM_API_KEY", raising=False)
    r = agent.run("anything")
    assert r.competitors and len(r.five_forces) == 5


def test_sample_cites_only_known_sources():
    r = agent.run("x", demo=True)
    assert r.cited_ids() <= {s.id for s in r.sources}


def test_markdown_sections():
    md = to_markdown(agent.run("x", demo=True))
    for h in ("## Competitors", "## Five forces", "## Key success factors", "## Risks", "## Sources"):
        assert h in md
    assert "[1]" in md


def test_missing_keys_rejected():
    with pytest.raises(ValueError):
        Report.from_dict("x", {"summary": {"claim": "a"}}, [])


def test_parse_json_fenced():
    assert llm.parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert llm.parse_json('{"a": 2}') == {"a": 2}


def test_parse_results_unwraps_redirect():
    page = '<a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fex.com%2Fa&rut=1">Ex &amp; Co</a>'
    assert parse_results(page, 5) == [("Ex & Co", "https://ex.com/a")]


def test_extract_text_strips_scripts():
    assert extract_text("<html><script>x()</script><p>Hello <b>world</b></p></html>") == "Hello world"


def test_live_path_with_mocks(monkeypatch):
    monkeypatch.setenv("RESEARCH_LLM_API_KEY", "test")
    monkeypatch.setattr(agent, "gather", lambda s: [Source(1, "t", "https://u", "text")])
    sample = json.loads((agent.SAMPLES / "french_accounting_saas.json").read_text())["report"]
    sample["risks"].append({"claim": "bad", "sources": [99]})
    monkeypatch.setattr(llm, "chat_json", lambda s, u: sample)
    with pytest.raises(ValueError, match="unknown source"):
        agent.run("x")


def test_gather_dedupes():
    srcs = agent.gather("x", searcher=lambda q, n: [("A", "https://a"), ("A", "https://a")], reader=lambda u: "body")
    assert len(srcs) == 1


def test_cli_writes_file(tmp_path, monkeypatch):
    monkeypatch.delenv("RESEARCH_LLM_API_KEY", raising=False)
    out = tmp_path / "r.md"
    assert main(["French accounting SaaS", "--demo", "--out", str(out)]) == 0
    assert out.read_text().startswith("# Market research")


def test_indicators_rendered_as_scores():
    r = agent.run("x", demo=True)
    r.indicators = [{"name": "switching_costs", "value": "high", "force": "buyer_power", "sources": [4]}]
    md = to_markdown(r)
    assert "Quantified force scores" in md and "switching_costs=high → 1 [4]" in md

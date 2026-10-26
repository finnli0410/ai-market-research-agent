import pytest

from research_agent.strategy import (Indicator, Evidence, cr, gross_margin_capture, hhi, hhi_band,
                                     industry_attractiveness, score_force, value_split, vrio)


def test_hhi_and_band():
    assert hhi([50, 50]) == 5000 and hhi_band(5000) == "highly concentrated"
    assert hhi_band(1500) == "moderately concentrated" and hhi_band(900) == "unconcentrated"
    assert cr([10, 40, 5, 30, 15]) == 95
    with pytest.raises(ValueError):
        hhi([60, 50])


def test_concentrated_growing_market_has_low_rivalry():
    f = score_force("rivalry", [Indicator("hhi", 5000, (1,)), Indicator("market_growth_pct", 30, (2,))])
    assert f.rating == "low" and f.sources == [1, 2]


def test_no_evidence_is_explicit():
    f = score_force("supplier_power", [Indicator("hhi", 5000, (1,))])
    assert f.score is None and f.rating == "insufficient evidence"


def test_attractiveness_ignores_unknown():
    a = score_force("rivalry", [Indicator("hhi", 6000, (1,))])            # score 1
    b = score_force("supplier_power", [])
    assert industry_attractiveness([a, b]) == 5


@pytest.mark.parametrize("flags,expected", [
    ((0, 1, 1, 1), "competitive disadvantage"), ((1, 0, 1, 1), "competitive parity"),
    ((1, 1, 0, 1), "temporary competitive advantage"), ((1, 1, 1, 0), "unexploited competitive advantage"),
    ((1, 1, 1, 1), "sustained competitive advantage")])
def test_vrio_ladder(flags, expected):
    assert vrio(*[Evidence(bool(f), "e", (1,)) for f in flags]) == expected


def test_vrio_requires_sources():
    with pytest.raises(ValueError):
        vrio(Evidence(True, "e", ()), Evidence(True, "e", (1,)), Evidence(True, "e", (1,)), Evidence(True, "e", (1,)))


def test_value_split():
    v = value_split(wtp=100, price=70, cost=40)
    assert (v.created, v.firm, v.buyer) == (60, 30, 30) and v.firm_share == 0.5
    with pytest.raises(ValueError):
        value_split(50, 70, 40)
    assert gross_margin_capture(100, 40) == 0.6

import pytest
from openseo.analyzers.qrg import analyze_qrg


def test_qrg_empty_text():
    res = analyze_qrg("")
    assert res["overall_quality"] == 0
    assert "empty-input" in res["flags"]
    assert res["tokens"] == 0


def test_qrg_filler_phrases():
    text = "It's important to note that we need to write high quality code. When it comes to writing tests, it goes without saying that we should be thorough."
    res = analyze_qrg(text)
    assert res["filler_score"] > 0
    assert "it's important to note that" in res["matches"]["filler"]
    assert "when it comes to" in res["matches"]["filler"]
    assert "it goes without saying" in res["matches"]["filler"]


def test_qrg_ai_patterns():
    text = "Let's delve into the rich tapestry of search engine optimization and navigate the complexities of content creation."
    res = analyze_qrg(text)
    assert res["ai_pattern_score"] > 0
    assert "delve into" in res["matches"]["ai_patterns"]
    assert "rich tapestry" in res["matches"]["ai_patterns"]
    assert "navigate the complexities" in res["matches"]["ai_patterns"]


def test_qrg_clean_content():
    # Content with high information density, proper names, numbers, no typical filler/AI patterns
    text = "Google released the PageSpeed Insights API in November 2018. The tool crawls pages and returns performance indicators like Largest Contentful Paint (LCP) and Cumulative Layout Shift (CLS)."
    res = analyze_qrg(text)
    assert res["filler_score"] == 0
    assert res["ai_pattern_score"] == 0
    assert res["overall_quality"] > 70

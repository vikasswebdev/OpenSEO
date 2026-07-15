import pytest
from openseo.models.page import Page
from openseo.models.issue import Severity, Category
from openseo.analyzers.title import analyze_title
from openseo.analyzers.meta import analyze_meta
from openseo.analyzers.headings import analyze_headings
from openseo.analyzers.images import analyze_images
from openseo.analyzers.links import analyze_links
from openseo.analyzers.schema_analyzer import analyze_schema
from openseo.analyzers.content import analyze_content

def test_analyze_title_missing():
    page = Page(url="https://example.com")
    issues, score = analyze_title(page)
    assert score == 0.0
    assert any(i.id == "title_missing" for i in issues)

def test_analyze_title_too_short():
    page = Page(url="https://example.com", title="Short")
    issues, score = analyze_title(page)
    assert score < 100.0
    assert any(i.id == "title_too_short" for i in issues)

def test_analyze_title_optimal():
    page = Page(url="https://example.com", title="This is a perfect page title with ideal length")
    issues, score = analyze_title(page)
    assert score == 100.0
    assert any(i.id == "title_length_ok" for i in issues)

def test_analyze_meta_missing():
    page = Page(url="https://example.com")
    issues, score = analyze_meta(page)
    assert score < 100.0
    assert any(i.id == "meta_desc_missing" for i in issues)

def test_analyze_headings_missing():
    page = Page(url="https://example.com")
    issues, score = analyze_headings(page)
    assert score == 0.0
    assert any(i.id == "headings_none" for i in issues)

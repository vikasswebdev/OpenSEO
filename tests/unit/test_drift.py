import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone

from openseo.services.drift_store import DriftStore, normalize_url, url_hash
from openseo.commands.drift import run_drift_rules
from openseo.models.page import Page, HeadingNode, OpenGraphData


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_drift.db"
        store = DriftStore(db_path)
        yield store
        store.close()


def test_url_normalization():
    url1 = "HTTPS://WWW.EXAMPLE.COM/page-path/?utm_source=fb&utm_medium=cpc&ref=xyz"
    url2 = "https://www.example.com/page-path?ref=xyz"
    
    assert normalize_url(url1) == "https://www.example.com/page-path?ref=xyz"
    assert normalize_url(url1) == normalize_url(url2)
    assert url_hash(url1) == url_hash(url2)


def test_drift_store_lifecycle(temp_db):
    store = temp_db
    
    baseline = {
        "url": "https://example.com/",
        "url_hash": url_hash("https://example.com/"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "title": "Old Title",
        "meta_description": "Old Meta Description",
        "canonical": "https://example.com/",
        "robots": "index, follow",
        "h1": "Old Heading",
        "h2_json": "[]",
        "h3_json": "[]",
        "schema_json": "[]",
        "og_json": "{}",
        "cwv_json": None,
        "html_hash": "abc123hash",
        "schema_hash": "xyzhash",
        "status_code": 200,
    }
    
    bid = store.save_baseline(baseline)
    assert bid > 0
    
    loaded = store.load_baseline("https://example.com/")
    assert loaded is not None
    assert loaded["id"] == bid
    assert loaded["title"] == "Old Title"
    
    # Save a comparison
    comparison = {
        "url": "https://example.com/",
        "summary": {"critical": 0, "warning": 1, "info": 0},
        "triggered_findings": []
    }
    cid = store.save_comparison(comparison, bid)
    assert cid > 0
    
    history = store.get_history("https://example.com/")
    assert len(history["baselines"]) == 1
    assert len(history["comparisons"]) == 1


def test_drift_comparison_rules():
    # Setup baseline dictionary
    baseline = {
        "id": 1,
        "url": "https://example.com/",
        "url_hash": url_hash("https://example.com/"),
        "timestamp": "2026-07-21T00:00:00Z",
        "title": "Baseline Page Title",
        "meta_description": "Baseline Page Description",
        "canonical": "https://example.com/",
        "robots": "index, follow",
        "h1": "Main Headline",
        "h2_json": '["Heading A", "Heading B"]',
        "h3_json": "[]",
        "schema_json": '[{"@type": "Article", "name": "Test"}]',
        "schema_hash": "oldschemadatahash",
        "og_json": '{"title": "Open Graph Title"}',
        "html_hash": "oldhtmlcontenthash",
        "status_code": 200,
    }

    # Test 1: Page matches perfectly
    matching_page = Page(
        url="https://example.com/",
        status_code=200,
        title="Baseline Page Title",
        meta_description="Baseline Page Description",
        canonical="https://example.com/",
        robots_meta="index, follow",
        headings=[
            HeadingNode(level=1, text="Main Headline"),
            HeadingNode(level=2, text="Heading A"),
            HeadingNode(level=2, text="Heading B"),
        ],
        schema_org=[{"@type": "Article", "name": "Test"}],
        open_graph=OpenGraphData(title="Open Graph Title"),
        body_text="Some text",
    )
    
    findings = run_drift_rules(baseline, matching_page)
    triggered = [f for f in findings if f["triggered"]]
    
    # We expect no critical or warning rules triggered
    assert len([f for f in triggered if f["severity"] in ("CRITICAL", "WARNING")]) == 0

    # Test 2: Drift introduced (e.g. title changed, schema removed)
    drifting_page = Page(
        url="https://example.com/",
        status_code=200,
        title="Brand New Page Title",  # Changed!
        meta_description="Baseline Page Description",
        canonical="https://example.com/",
        robots_meta="noindex, follow",  # Added noindex!
        headings=[
            HeadingNode(level=2, text="Heading A"),  # H1 removed!
        ],
        schema_org=[],  # Schema removed!
        open_graph=OpenGraphData(),  # OG tags removed!
        body_text="Some text",
    )

    findings = run_drift_rules(baseline, drifting_page)
    triggered = [f for f in findings if f["triggered"]]
    
    # Verify specific rules are triggered
    triggered_rules = {f["rule"] for f in triggered}
    assert "title_changed" in triggered_rules
    assert "noindex_added" in triggered_rules
    assert "h1_removed" in triggered_rules
    assert "schema_removed" in triggered_rules
    assert "og_tags_removed" in triggered_rules

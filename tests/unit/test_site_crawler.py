import pytest
from openseo.crawler.site_crawler import SiteCrawler, normalize_url
from openseo.analyzers.link_graph import build_link_graph
from openseo.analyzers.duplicates import detect_duplicate_clusters, compute_normalized_text_hash
from openseo.models.page import Page, LinkData


def test_normalize_url():
    assert normalize_url("HTTPS://EXAMPLE.COM/") == "https://example.com"
    assert normalize_url("https://example.com/about/") == "https://example.com/about"
    assert normalize_url("https://example.com/about?query=1#frag") == "https://example.com/about?query=1"


def test_link_graph_builder():
    pages = {
        "https://example.com": Page(
            url="https://example.com",
            links=[
                LinkData(href="https://example.com/about", is_external=False),
                LinkData(href="https://example.com/contact", is_external=False),
            ]
        ),
        "https://example.com/about": Page(
            url="https://example.com/about",
            links=[LinkData(href="https://example.com", is_external=False)]
        ),
        "https://example.com/contact": Page(
            url="https://example.com/contact",
            links=[]
        ),
        "https://example.com/orphan": Page(
            url="https://example.com/orphan",
            links=[]
        )
    }

    graph = build_link_graph(pages)
    
    assert len(graph) == 4
    # Home node should point to /about and /contact
    assert "https://example.com/about" in graph["https://example.com"].out_links
    assert "https://example.com/contact" in graph["https://example.com"].out_links
    
    # Check incoming count
    assert "https://example.com" in graph["https://example.com/about"].in_links
    
    # Check orphan page
    assert graph["https://example.com/orphan"].is_orphan is True
    assert graph["https://example.com"].is_orphan is False


def test_duplicate_clusters():
    pages = {
        "https://example.com/page1": Page(
            url="https://example.com/page1",
            body_text="This is unique body text number one."
        ),
        "https://example.com/page2": Page(
            url="https://example.com/page2",
            body_text="Some duplicate content here."
        ),
        "https://example.com/page3": Page(
            url="https://example.com/page3",
            body_text="some duplicate content here!"
        ),
    }

    clusters = detect_duplicate_clusters(pages)
    assert len(clusters) == 1
    cluster = clusters[0]
    assert len(cluster.urls) == 2
    assert "https://example.com/page2" in cluster.urls
    assert "https://example.com/page3" in cluster.urls

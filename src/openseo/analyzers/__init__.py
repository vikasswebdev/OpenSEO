"""Analyzers package."""

from openseo.analyzers.content import analyze_content
from openseo.analyzers.headings import analyze_headings
from openseo.analyzers.images import analyze_images
from openseo.analyzers.links import analyze_links
from openseo.analyzers.meta import analyze_meta
from openseo.analyzers.schema_analyzer import analyze_schema
from openseo.analyzers.title import analyze_title
from openseo.analyzers.technical import analyze_page_technical, analyze_site_technical
from openseo.analyzers.duplicates import detect_duplicate_clusters
from openseo.analyzers.link_graph import build_link_graph
from openseo.analyzers.qrg import analyze_qrg

__all__ = [
    "analyze_title",
    "analyze_meta",
    "analyze_headings",
    "analyze_images",
    "analyze_links",
    "analyze_schema",
    "analyze_content",
    "analyze_page_technical",
    "analyze_site_technical",
    "detect_duplicate_clusters",
    "build_link_graph",
    "analyze_qrg",
]

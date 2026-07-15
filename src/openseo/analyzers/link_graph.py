"""
Internal linking directed link graph builder and popularity analysis.
"""

from __future__ import annotations

from urllib.parse import urlparse
from openseo.models.page import Page
from openseo.models.site import LinkNode
from openseo.crawler.site_crawler import normalize_url


def build_link_graph(pages: dict[str, Page]) -> dict[str, LinkNode]:
    """
    Builds a directed internal link graph of the site.

    Tracks incoming and outgoing links along with their associated anchor texts.
    """
    graph: dict[str, LinkNode] = {
        url: LinkNode(url=url) for url in pages
    }

    for src_url, page in pages.items():
        src_node = graph.setdefault(src_url, LinkNode(url=src_url))

        for link in page.internal_links:
            dest_url = normalize_url(link.href)

            # Ensure we only track links that are within the crawled page set
            if dest_url in pages:
                dest_node = graph.setdefault(dest_url, LinkNode(url=dest_url))

                # Add to outgoing links if not already present
                if dest_url not in src_node.out_links:
                    src_node.out_links.append(dest_url)

                # Add to incoming links if not already present
                if src_url not in dest_node.in_links:
                    dest_node.in_links.append(src_url)

                # Track anchor text
                anchor = (link.text or "").strip()
                if anchor:
                    anchor_texts = dest_node.anchor_texts.setdefault(src_url, [])
                    if anchor not in anchor_texts:
                        anchor_texts.append(anchor)

    return graph

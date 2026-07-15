"""
Content hash-based duplicate page detector.
"""

from __future__ import annotations

import hashlib
import re
from openseo.models.page import Page
from openseo.models.site import DuplicateCluster


def compute_normalized_text_hash(text: str) -> str:
    """Normalize text by converting to lowercase, stripping punctuation, and hashing."""
    # Remove HTML tags (if any) and normalize whitespace
    cleaned = re.sub(r"\s+", " ", text.lower().strip())
    # Remove punctuation
    cleaned = re.sub(r"[^\w\s]", "", cleaned)
    # Generate MD5 hash
    return hashlib.md5(cleaned.encode("utf-8")).hexdigest()


def detect_duplicate_clusters(pages: dict[str, Page]) -> list[DuplicateCluster]:
    """
    Cluster pages by content hash. Any cluster with size > 1 is a duplicate cluster.
    """
    hash_map: dict[str, list[str]] = {}

    for url, page in pages.items():
        if not page.body_text:
            continue
        text_hash = compute_normalized_text_hash(page.body_text)
        hash_map.setdefault(text_hash, []).append(url)

    clusters = []
    for text_hash, urls in hash_map.items():
        if len(urls) > 1:
            clusters.append(
                DuplicateCluster(
                    content_hash=text_hash,
                    urls=urls,
                )
            )

    return clusters

"""
QRG-aligned content quality detector for OpenSEO.

Ported from claude-seo's content_quality.py script.
Scores text against Google's January 23, 2025 Quality Rater Guidelines update:
  - §4.6.5 Scaled content abuse (using low-effort templates or AI generators)
  - §4.6.6 MC (Main Content) copied or AI-generated without value
  - §4.6 Filler content (padding phrases, low information density)
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Iterable, TypedDict


class QRGAnalysisResult(TypedDict):
    filler_score: int
    ai_pattern_score: int
    information_density: float
    repetition_score: int
    overall_quality: int
    flags: list[str]
    matches: dict[str, list[str]]
    tokens: int
    unique_tokens: int


# Padding / filler phrases that QRG §4.6 flags as "little-to-no value".
FILLER_PHRASES: tuple[str, ...] = (
    "it's important to note that",
    "in this article, we'll explore",
    "in this article we will explore",
    "in today's fast-paced world",
    "in today's digital age",
    "in today's competitive landscape",
    "needless to say",
    "at the end of the day",
    "when it comes to",
    "when all is said and done",
    "in the realm of",
    "in the world of",
    "the bottom line is",
    "without further ado",
    "first and foremost",
    "last but not least",
    "for what it's worth",
    "it goes without saying",
    "as we all know",
    "the truth is that",
    "the fact of the matter is",
    "more often than not",
    "let's dive in",
    "let's dive into",
    "let's take a closer look",
    "let's take a deeper look",
)


# LLM-typical phrasings (Wikipedia AI Cleanup catalogue, CC BY-SA 4.0;
# also used by ivankuznetsov/claude-seo, MIT).
AI_PATTERNS: tuple[str, ...] = (
    "delve into",
    "delve deeper into",
    "in the ever-evolving",
    "ever-evolving landscape",
    "ever-changing landscape",
    "in the dynamic landscape",
    "navigating the",
    "navigate the complexities",
    "tapestry of",
    "rich tapestry",
    "intricate tapestry",
    "embark on a journey",
    "embarking on this",
    "a testament to",
    "a beacon of",
    "the cornerstone of",
    "a cornerstone of",
    "at the heart of",
    "at its core",
    "in essence,",
    "in conclusion,",
    "ultimately,",
    "moreover,",
    "furthermore,",
    "however, it's worth noting",
    "it's worth noting that",
    "by leveraging",
    "leverage the power of",
    "leveraging the power of",
    "harness the power of",
    "unlock the potential",
    "unlock the full potential",
    "the realm of possibilities",
    "open up a world of",
    "a world of possibilities",
    "elevate your",
    "transform your",
    "revolutionize the way",
    "game-changer",
    "game-changing",
    "cutting-edge",
    "state-of-the-art",
    "in summary,",
    "to summarize,",
    "to put it simply,",
    "in a nutshell,",
)


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?(?:%|st|nd|rd|th)?\b")
# Capitalised multi-word names: rough proper-noun heuristic. Two or more
# capitalised tokens in a row count as one entity.
ENTITY_RE = re.compile(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")


def _count_phrase_hits(text: str, patterns: Iterable[str]) -> list[str]:
    """Return the patterns that appear at least once in text (case-insensitive)."""
    lowered = text.lower()
    return [p for p in patterns if p in lowered]


def _repetition_score(tokens: list[str]) -> float:
    """Bigram repetition: fraction of bigrams that recur more than once."""
    if len(tokens) < 4:
        return 0.0
    bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
    counts = Counter(bigrams)
    repeated = sum(1 for v in counts.values() if v > 1)
    return repeated / max(1, len(counts))


def analyze_qrg(text: str) -> QRGAnalysisResult:
    """Score a body of text against the QRG quality heuristics."""
    if not text or not text.strip():
        return {
            "filler_score": 0,
            "ai_pattern_score": 0,
            "information_density": 0.0,
            "repetition_score": 0,
            "overall_quality": 0,
            "flags": ["empty-input"],
            "matches": {"filler": [], "ai_patterns": []},
            "tokens": 0,
            "unique_tokens": 0,
        }

    tokens = [t.lower() for t in TOKEN_RE.findall(text)]
    n_tokens = len(tokens)
    unique = len(set(tokens))

    filler_hits = _count_phrase_hits(text, FILLER_PHRASES)
    ai_hits = _count_phrase_hits(text, AI_PATTERNS)

    # Density: entities + numbers per 100 tokens. A typical high-density
    # article lands at ~5+; a generic filler post lands at <2.
    entities = len(ENTITY_RE.findall(text))
    numbers = len(NUMBER_RE.findall(text))
    density_per_100 = (entities + numbers) * 100.0 / max(1, n_tokens)
    information_density = min(1.0, density_per_100 / 10.0)

    rep = _repetition_score(tokens)
    rep_score = int(round(rep * 100))

    # Scale to per-1000 tokens so the score is comparable across page lengths.
    scale = max(1.0, n_tokens / 1000.0)
    filler_per_kt = len(filler_hits) / scale
    ai_per_kt = len(ai_hits) / scale

    filler_score = min(100, int(round(filler_per_kt * 25)))
    ai_pattern_score = min(100, int(round(ai_per_kt * 15)))

    flags: list[str] = []
    if filler_score >= 50:
        flags.append("filler")
    if ai_pattern_score >= 40:
        flags.append("ai-patterns")
    if information_density < 0.20:
        flags.append("low-density")
    if rep_score >= 30:
        flags.append("repetitive")
    if n_tokens < 300:
        flags.append("thin-content")

    # Composite: invert penalty signals, weight by impact.
    overall = (
        (100 - filler_score) * 0.25
        + (100 - ai_pattern_score) * 0.25
        + information_density * 100 * 0.25
        + (100 - rep_score) * 0.15
        + min(100, n_tokens / 10.0) * 0.10  # length bonus capped at 1000 tokens
    )

    return {
        "filler_score": filler_score,
        "ai_pattern_score": ai_pattern_score,
        "information_density": round(information_density, 3),
        "repetition_score": rep_score,
        "overall_quality": int(round(overall)),
        "flags": flags,
        "matches": {"filler": filler_hits, "ai_patterns": ai_hits},
        "tokens": n_tokens,
        "unique_tokens": unique,
    }

# ============================================================================
# TECHNICAL TERM AUTO-DETECTOR
#
# Flags likely domain/technical terms in an English MCQ stem or option for
# human confirmation before they're locked into the glossary and protected
# from translation. This implements your stated preference: "Auto-detect:
# tool flags likely technical terms... for you to confirm/edit."
#
# Heuristics used (deliberately simple & inspectable, not ML-based, so a
# reviewer can see exactly why something got flagged):
#   1. Already in the glossary -> always flagged (high confidence)
#   2. Multi-word noun phrases matching common trade-term shapes
#      (e.g. "X gap", "X lining", "X repair", "X installation")
#   3. Capitalized non-sentence-initial words (proper-noun-like)
#   4. Words with no common-English-word match (rough heuristic: not in
#      a small stopword/common-word allowlist) AND appearing in a
#      technical-sounding suffix pattern (-ing, -tion, -ment, -ory)
#
# This is intentionally conservative — it's a SUGGESTION list for a human
# to approve/edit/reject per row, not an automatic decision.
# ============================================================================

import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "glossaries"))
from glossary import GLOSSARY, all_terms

COMMON_WORDS = {
    "the", "is", "are", "was", "were", "be", "been", "being", "a", "an",
    "to", "of", "in", "on", "at", "for", "with", "by", "from", "as", "should",
    "must", "can", "could", "will", "would", "shall", "and", "or", "but",
    "not", "no", "yes", "all", "above", "below", "before", "after", "during",
    "while", "ensure", "done", "used", "this", "that", "these", "those",
    "which", "what", "when", "where", "who", "how", "why", "general",
    "means", "leads", "required", "generally", "applied", "company",
    "rule", "audit", "purpose", "decoration", "safety", "only", "both",
    "and b", "manual", "throwing", "proper", "handling", "tools", "floor",
    "vehicle", "parking", "material", "materials", "availability", "area",
    "clearance", "quantity", "usage", "weight", "strength", "color", "test",
    "thickness", "effect", "performance", "cracks", "mixed", "specification",
    "randomly", "very", "dry", "wet", "clean", "oily", "painted", "new",
    "construction", "demolition", "increase", "reduce", "avoid", "save",
    "remove", "improve", "change", "left", "collected", "discarded", "reused",
    "during", "must", "stacking", "cleanliness",
}

# Trade-term shape patterns: "<word(s)> <trigger noun>" or "<trigger> <word>"
TRADE_PATTERNS = [
    r"\b\w+\s+(?:gap|lining|repair|installation|curing|loss)\b",
    r"\b(?:expansion|module|brick|patch|wet|dry)\s+\w+\b",
]

TECHNICAL_SUFFIXES = ("ory", "tion", "ment", "ing")

def candidate_terms(text, existing_glossary_only=False):

    if text is None:
        return []

    text = str(text).strip()

    if text == "" or text.lower() == "nan":
        return []

    found = {}

    lower_text = text.lower()

    for term in sorted(all_terms(), key=lambda x: len(str(x)), reverse=True):

        term = str(term).lower()

        if term in lower_text:

            found[term] = {
                "term": term,
                "reason": "Known glossary term",
                "in_glossary": True
            }

            lower_text = lower_text.replace(term, " " * len(term))

    if existing_glossary_only:
        return list(found.values())

    for pattern in TRADE_PATTERNS:

        for m in re.finditer(pattern, text, re.IGNORECASE):

            phrase = m.group(0).strip().lower()

            if phrase not in found:

                found[phrase] = {
                    "term": phrase,
                    "reason": "Matches trade-term pattern",
                    "in_glossary": False
                }

    words = text.split()

    for i, w in enumerate(words):

        clean = re.sub(r"[^\w\-]", "", w)

        if not clean:
            continue

        if (
            i > 0
            and clean[0].isupper()
            and clean.lower() not in COMMON_WORDS
            and clean.lower() not in found
        ):

            found[clean.lower()] = {
                "term": clean,
                "reason": "Capitalized",
                "in_glossary": False
            }

    for w in words:

        clean = re.sub(r"[^\w\-]", "", w).lower()

        if len(clean) < 5:
            continue

        if clean in COMMON_WORDS:
            continue

        if clean.endswith(("ory", "ment")):

            found.setdefault(
                clean,
                {
                    "term": clean,
                    "reason": "Technical suffix",
                    "in_glossary": False
                }
            )

        elif clean.endswith(("ing", "tion")) and len(clean) >= 8:

            found.setdefault(
                clean,
                {
                    "term": clean,
                    "reason": "Technical suffix",
                    "in_glossary": False
                }
            )

    return list(found.values())


def scan_row(question, options):
    """Scan a full MCQ row and safely detect technical terms."""

    all_candidates = {}

    texts = []

    # Question
    if question is not None:
        texts.append(str(question))

    # Options
    for opt in options:
        if opt is None:
            continue

        value = str(opt).strip()

        if value == "" or value.lower() == "nan":
            continue

        texts.append(value)

    for text in texts:

        try:
            candidates = candidate_terms(str(text))

            for c in candidates:
                key = str(c["term"]).lower()

                if key not in all_candidates:
                    all_candidates[key] = c

        except Exception as e:
            print("Skipping invalid value:", repr(text), e)

    return list(all_candidates.values())

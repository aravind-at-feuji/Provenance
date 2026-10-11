"""
agents/validators/evidence_span.py — Verification of extracted character offsets against source text.

Architecture reference: §J.2 Agent 1, §Q.7 Layer 5.
"Extracted claims must map to real character offsets in the source — fabricated content
is detected mechanically. If a span doesn't exist in the source, the extraction is
rejected as hallucinated."
"""

from __future__ import annotations

import re
from typing import Sequence

from agents.schemas.event_extraction import EventExtraction, TextSpan


def _normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def validate_text_span(source_text: str, span: TextSpan) -> tuple[bool, str | None]:
    """
    Validate a single TextSpan against source_text.
    Returns (True, None) if valid, or (False, reason) if invalid/hallucinated.
    """
    if span.start < 0 or span.end > len(source_text) or span.start >= span.end:
        return (
            False,
            f"Offset out of bounds: [{span.start}:{span.end}] for source text of length {len(source_text)}",
        )

    actual_substring = source_text[span.start : span.end]
    expected_text = span.text

    # Exact match check
    if actual_substring == expected_text:
        return True, None

    # Normalization check (e.g. slight whitespace variance or trailing punctuation)
    if _normalize_whitespace(actual_substring) == _normalize_whitespace(expected_text):
        return True, None

    return (
        False,
        f"Hallucinated span: offset [{span.start}:{span.end}] contains '{actual_substring}', "
        f"expected '{expected_text}'",
    )


def validate_evidence_spans(
    source_text: str, extraction: EventExtraction
) -> tuple[bool, list[str]]:
    """
    Mechanical verification of all evidence spans and entity text spans in an EventExtraction.

    Returns:
        (is_valid, error_messages)
    """
    errors: list[str] = []

    # If extraction is marked not relevant, evidence spans may be empty
    if not extraction.is_relevant:
        return True, []

    # At least one evidence span required for relevant events (Engineering rule 9, arch §J.2)
    if not extraction.evidence_spans:
        errors.append("Evidence required: relevant event extraction contains 0 evidence_spans")

    # Validate each evidence span
    for idx, span in enumerate(extraction.evidence_spans):
        valid, err = validate_text_span(source_text, span)
        if not valid:
            errors.append(f"evidence_spans[{idx}]: {err}")

    # Validate each entity mention text span
    for idx, entity in enumerate(extraction.affected_entities):
        valid, err = validate_text_span(source_text, entity.text_span)
        if not valid:
            errors.append(f"affected_entities[{idx}] ('{entity.name}'): {err}")

    return len(errors) == 0, errors

"""
app/modules/ai/extraction.py — Event Extraction Agent bridge.
"""

from agents.extraction import EventExtractionAgent
from agents.schemas.event_extraction import (
    EntityMention,
    EventExtraction,
    EventExtractionResult,
    EventTypeEnum,
    TextSpan,
)

__all__ = [
    "EntityMention",
    "EventExtraction",
    "EventExtractionAgent",
    "EventExtractionResult",
    "EventTypeEnum",
    "TextSpan",
]

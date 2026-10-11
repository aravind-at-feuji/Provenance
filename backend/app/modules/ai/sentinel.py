"""
app/modules/ai/sentinel.py — Injection sentinel bridge.
"""

from agents.sentinel import (
    InjectionScanResult,
    InjectionSentinel,
    wrap_untrusted_content,
)

__all__ = [
    "InjectionScanResult",
    "InjectionSentinel",
    "wrap_untrusted_content",
]

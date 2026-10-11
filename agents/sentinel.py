"""
agents/sentinel.py — Prompt injection detection & structural untrusted content wrapper.

Architecture reference: §Q.7 Prompt Injection — the core LLM threat (Layers 1 & 6).
All external content (news articles, regulatory filings, invoices) is assumed adversarial.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence


def wrap_untrusted_content(content: str) -> str:
    """
    Wrap untrusted external content in structural XML delimiters.
    Sanitizes closing delimiter tags inside content to prevent injection breakout (arch §Q.7 Layer 1).
    """
    # Neutralize closing tag breakout attempts
    sanitized = re.sub(
        r"</\s*untrusted_content\s*>",
        "&lt;/untrusted_content&gt;",
        content,
        flags=re.IGNORECASE,
    )
    # Neutralize faux system delimiters
    sanitized = re.sub(
        r"<\s*system\s*>",
        "&lt;system&gt;",
        sanitized,
        flags=re.IGNORECASE,
    )
    sanitized = re.sub(
        r"</\s*system\s*>",
        "&lt;/system&gt;",
        sanitized,
        flags=re.IGNORECASE,
    )
    return f"<untrusted_content>\n{sanitized}\n</untrusted_content>"


@dataclass
class InjectionScanResult:
    """Security assessment result from scanning untrusted input text."""

    is_suspicious: bool
    risk_score: float  # 0.0 to 1.0
    matched_patterns: list[str] = field(default_factory=list)
    action_recommended: str = "allow"  # allow | needs_review | block


class InjectionSentinel:
    """
    Heuristic, pattern-based, and structural sentinel detector for adversarial
    prompt injection attempts in external regulatory feeds and uploaded documents.
    """

    ADVERSARIAL_RULES: list[tuple[str, re.Pattern, float]] = [
        # Direct instruction overrides
        (
            "override_ignore_previous",
            re.compile(
                r"\b(ignore|disregard|forget|override|bypass)\s+(all\s+)?(previous|prior|above|former|your)?\s*(instructions|directives|prompts|rules|guidelines)\b",
                re.IGNORECASE,
            ),
            0.95,
        ),
        (
            "override_new_instructions",
            re.compile(
                r"\b(new\s+(instructions|directives|system\s+prompt|role|task)|your\s+new\s+task\s+is)\b",
                re.IGNORECASE,
            ),
            0.85,
        ),
        (
            "override_from_now_on",
            re.compile(
                r"\b(from\s+now\s+on\s+you\s+(are|will|must)|starting\s+now\s+act\s+as)\b",
                re.IGNORECASE,
            ),
            0.85,
        ),
        (
            "override_multilingual_french",
            re.compile(
                r"\b(ignorer\s+(toutes\s+)?(les\s+)?instructions)\b",
                re.IGNORECASE,
            ),
            0.90,
        ),
        # Roleplay & Jailbreak
        (
            "jailbreak_dan_mode",
            re.compile(
                r"\b(dan\s+mode|do\s+anything\s+now|jailbreak|unrestricted\s+ai|developer\s+mode\s+enabled)\b",
                re.IGNORECASE,
            ),
            0.95,
        ),
        (
            "roleplay_pretend_admin",
            re.compile(
                r"\b(pretend\s+you\s+are|act\s+as\s+a\s+system\s+administrator|simulate\s+root)\b",
                re.IGNORECASE,
            ),
            0.80,
        ),
        # Delimiter escapes & system tags
        (
            "delimiter_breakout",
            re.compile(
                r"(</untrusted_content>|<system>|\[system\]|system:\s*|human:\s*|assistant:\s*|###\s*system|\]\]>)",
                re.IGNORECASE,
            ),
            0.90,
        ),
        # System prompt extraction & leak attempts
        (
            "prompt_leak_attempt",
            re.compile(
                r"\b(print|reveal|show|display|output|repeat|dump)\s+(your\s+)?(system\s+prompt|hidden\s+instructions|initial\s+prompt)\b",
                re.IGNORECASE,
            ),
            0.90,
        ),
        (
            "verbatim_directive_request",
            re.compile(
                r"\b(repeat\s+everything\s+above|what\s+are\s+your\s+instructions)\b",
                re.IGNORECASE,
            ),
            0.85,
        ),
        # Forced output hijacking
        (
            "forced_output_token",
            re.compile(
                r"\b(output\s+access\s+granted|reply\s+with\s+(only\s+)?['\"]?access\s+granted['\"]?|say\s+pwned|print\s+['\"]?hacked['\"]?|output\s+only\s+the\s+word|force\s+output|admin_override)",
                re.IGNORECASE,
            ),
            0.90,
        ),
        (
            "forced_compromised_token",
            re.compile(
                r"\b(word\s+compromised|say\s+hacked|say\s+pwned)\b",
                re.IGNORECASE,
            ),
            0.90,
        ),
        (
            "exfiltration_command",
            re.compile(
                r"(\bcurl\s+http|\bwget\s+http|fetch\s*\(|\bexfiltrate|\bsend\s+api\s+key)",
                re.IGNORECASE,
            ),
            0.95,
        ),
    ]

    @classmethod
    def scan(cls, text: str, threshold: float = 0.70) -> InjectionScanResult:
        """
        Scan text for instruction-injection markers.
        """
        if not text:
            return InjectionScanResult(is_suspicious=False, risk_score=0.0)

        matched_names: list[str] = []
        max_score = 0.0

        for rule_name, pattern, score in cls.ADVERSARIAL_RULES:
            if pattern.search(text):
                matched_names.append(rule_name)
                if score > max_score:
                    max_score = score

        is_suspicious = max_score >= threshold
        action = "needs_review" if is_suspicious else "allow"

        return InjectionScanResult(
            is_suspicious=is_suspicious,
            risk_score=max_score,
            matched_patterns=matched_names,
            action_recommended=action,
        )

"""
agents/extraction.py — Event Extraction Agent (Agent 1).

Architecture reference: §J.2 Agent 1, §F.1 Extract, §Q.7 Prompt Injection defence.
Pure unstructured-to-structured NLP extractor with:
  - Zero tools (tool-less ingestion to eliminate execution surfaces)
  - <untrusted_content> tag wrapping
  - Injection sentinel pre-scanning
  - Evidence-span mechanical validation
  - Retries with error feedback (up to 2 attempts) -> needs_review fallback
  - Strictly typed EventExtraction schema output
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from agents.gateway import LLMGateway
from agents.schemas.event_extraction import (
    EventExtraction,
    EventExtractionResult,
    EventTypeEnum,
)
from agents.sentinel import InjectionSentinel, wrap_untrusted_content
from agents.validators.evidence_span import validate_evidence_spans

logger = structlog.get_logger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt_template(agent_name: str, version: str = "v1") -> str:
    """Load versioned system prompt from agents/prompts/<agent_name>/<version>.md."""
    prompt_path = _PROMPTS_DIR / agent_name / f"{version}.md"
    if prompt_path.is_file():
        return prompt_path.read_text(encoding="utf-8")
    # Fallback to txt extension
    txt_path = _PROMPTS_DIR / agent_name / f"{version}.txt"
    if txt_path.is_file():
        return txt_path.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Prompt template not found for {agent_name} {version} at {prompt_path}")


class EventExtractionAgent:
    """
    Agent 1 — Event Extraction Agent.
    Transforms raw unstructured source text into validated EventExtraction models.
    """

    def __init__(
        self,
        gateway: LLMGateway | None = None,
        db: AsyncSession | None = None,
        prompt_version: str = "v1",
    ) -> None:
        self.gateway = gateway or LLMGateway(db=db)
        self.prompt_version = prompt_version
        self._system_prompt = load_prompt_template("event_extraction", prompt_version)

    async def extract(
        self,
        *,
        title: str | None = None,
        body_text: str | None = None,
        source_url: str | None = None,
        source_type: str = "live",
        published_date: str | None = None,
        source_reliability: str = "high",
        max_retries: int = 2,
    ) -> EventExtractionResult:
        """
        Execute event extraction with multi-layer prompt injection defence,
        schema enforcement, and evidence-span mechanical validation.
        """
        full_text = ""
        if title and body_text:
            full_text = f"Title: {title.strip()}\n\nBody: {body_text.strip()}"
        elif title:
            full_text = f"Title: {title.strip()}"
        elif body_text:
            full_text = body_text.strip()
        else:
            return EventExtractionResult(
                status="extraction_failed",
                validation_errors=["Empty input text: both title and body_text are missing"],
            )

        # 1. Pre-extraction scan with Injection Sentinel (arch §Q.7 Layer 6)
        sentinel_res = InjectionSentinel.scan(full_text)
        is_suspicious_injection = sentinel_res.is_suspicious

        # 2. Structural untrusted content encapsulation (arch §Q.7 Layer 1)
        wrapped_content = wrap_untrusted_content(full_text)

        metadata_header = (
            f"SOURCE METADATA:\n"
            f"- URL: {source_url or 'N/A'}\n"
            f"- Type: {source_type}\n"
            f"- Reliability: {source_reliability}\n"
            f"- Published: {published_date or 'N/A'}\n\n"
        )
        user_prompt = f"{metadata_header}Analyze the following external record:\n{wrapped_content}"

        last_errors: list[str] = []
        model_used = self.gateway.resolve_model_for_task("extraction")

        for attempt in range(max_retries + 1):
            try:
                extraction = await self.gateway.execute_structured(
                    task="extraction",
                    prompt=user_prompt,
                    schema=EventExtraction,
                    system_prompt=self._system_prompt,
                    prompt_version=self.prompt_version,
                )

                # 3. Evidence-span mechanical verification (arch §Q.7 Layer 5, §J.2)
                valid, span_errors = validate_evidence_spans(full_text, extraction)
                if not valid:
                    last_errors = span_errors
                    logger.warning(
                        "extraction_evidence_spans_invalid",
                        attempt=attempt,
                        errors=span_errors,
                    )
                    if attempt < max_retries:
                        # Feed specific error back to model for surgical correction
                        feedback = (
                            f"\n\nERROR IN PREVIOUS EXTRACTION ATTEMPT:\n"
                            f"The following evidence spans failed character-offset verification in the source text:\n"
                            + "\n".join(f"- {e}" for e in span_errors)
                            + "\nPlease re-extract ONLY exact verbatim character spans that exist in the text."
                        )
                        user_prompt = user_prompt + feedback
                        continue
                    else:
                        # Max retries exceeded -> flag as needs_review, never create a corrupt event
                        combined_errors = (
                            [f"Sentinel warning: {p}" for p in sentinel_res.matched_patterns]
                            if is_suspicious_injection
                            else []
                        ) + span_errors
                        return EventExtractionResult(
                            extraction=extraction,
                            status="needs_review",
                            validation_errors=combined_errors,
                            raw_prompt=user_prompt,
                            model_used=model_used,
                            prompt_version=self.prompt_version,
                        )

                # If injection sentinel detected suspicious patterns, mark for human review
                status = "needs_review" if is_suspicious_injection else "success"
                initial_errors = (
                    [f"Sentinel warning: {p}" for p in sentinel_res.matched_patterns]
                    if is_suspicious_injection
                    else []
                )

                return EventExtractionResult(
                    extraction=extraction,
                    status=status,
                    validation_errors=initial_errors,
                    raw_prompt=user_prompt,
                    model_used=model_used,
                    prompt_version=self.prompt_version,
                )

            except Exception as exc:
                last_errors = [str(exc)]
                logger.error("extraction_attempt_failed", attempt=attempt, error=str(exc))
                if attempt < max_retries:
                    continue

        combined_errors = (
            [f"Sentinel warning: {p}" for p in sentinel_res.matched_patterns]
            if is_suspicious_injection
            else []
        ) + last_errors
        return EventExtractionResult(
            extraction=None,
            status="needs_review",
            validation_errors=combined_errors,
            raw_prompt=user_prompt,
            model_used=model_used,
            prompt_version=self.prompt_version,
        )

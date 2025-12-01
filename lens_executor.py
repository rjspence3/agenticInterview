"""
Lens Executor - Executes lens analysis on interview sessions.

This module applies lenses to completed interview sessions, calling the LLM
to analyze transcripts and storing structured results in the database.
"""

import json
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from db_models import (
    Lens, LensResult, LensCriterionResult, LensResultStatus,
    InterviewSession, TranscriptEntry
)
from lens_prompt_builder import build_lens_prompt
from llm_client import LLMClient
from error_handling import sanitize_error_message
from logging_config import get_logger

logger = get_logger(__name__)


class LensExecutor:
    """
    Executes lens analysis on interview sessions using LLMs.

    Handles the complete pipeline:
    1. Fetch session and transcript from database
    2. Build lens-specific prompt
    3. Call LLM
    4. Parse and validate response
    5. Store results in database
    """

    def __init__(
        self,
        llm_client: LLMClient,
        model: str = "gpt-4",
        temperature: float = 0.3
    ):
        """
        Initialize the lens executor.

        Args:
            llm_client: LLM client instance for making API calls
            model: Model name to use for analysis
            temperature: Temperature for LLM calls (lower = more deterministic)
        """
        self.llm_client = llm_client
        self.model = model
        self.temperature = temperature

    def execute_lens(
        self,
        db: Session,
        session_id: int,
        lens_id: int
    ) -> LensResult:
        """
        Execute a lens on an interview session.

        Args:
            db: Database session
            session_id: ID of the InterviewSession to analyze
            lens_id: ID of the Lens to apply

        Returns:
            LensResult object with status and results

        Raises:
            ValueError: If session or lens not found, or session not completed
        """
        # Fetch session and lens
        session = db.get(InterviewSession, session_id)
        if not session:
            raise ValueError(f"InterviewSession {session_id} not found")

        lens = db.get(Lens, lens_id)
        if not lens:
            raise ValueError(f"Lens {lens_id} not found")

        # Verify session is completed
        if session.status.value != "completed":
            raise ValueError(f"Session {session_id} is not completed (status: {session.status.value})")

        # Get transcript
        transcript = list(session.transcript)
        if not transcript:
            raise ValueError(f"Session {session_id} has no transcript")

        logger.info(f"Starting lens execution: session_id={session_id}, lens_id={lens_id}, lens_name='{lens.name}'")

        # Create LensResult record (status=in_progress)
        lens_result = LensResult(
            session_id=session_id,
            lens_id=lens_id,
            status=LensResultStatus.IN_PROGRESS,
            llm_provider=self._get_provider_name(),
            llm_model=self.model,
            created_at=datetime.now()
        )
        db.add(lens_result)
        db.flush()  # Get the ID

        try:
            # Build prompt
            prompt = build_lens_prompt(lens, session, transcript)
            logger.debug(f"Built lens prompt: session_id={session_id}, lens_id={lens_id}, prompt_length={len(prompt)}")

            # Call LLM
            response_text = self.llm_client.call_llm(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature
            )

            # Parse response
            parsed_results = self._parse_llm_response(response_text, lens)
            logger.info(f"Parsed lens response: session_id={session_id}, lens_id={lens_id}, criteria_count={len(parsed_results)}")

            # Store criterion results
            for criterion_data in parsed_results:
                criterion_result = LensCriterionResult(
                    lens_result_id=lens_result.id,
                    criterion_name=criterion_data["criterion"],
                    score=criterion_data.get("score"),
                    scale=lens.config.get("scoring_scale", "0-5"),
                    flags=criterion_data.get("flags", []),
                    extracted_items=criterion_data.get("extracted_items", []),
                    supporting_quotes=criterion_data.get("supporting_quotes", []),
                    notes=criterion_data.get("notes")
                )
                db.add(criterion_result)

            # Mark as completed
            lens_result.status = LensResultStatus.COMPLETED
            lens_result.completed_at = datetime.now()
            db.flush()

            logger.info(f"Lens execution completed: session_id={session_id}, lens_id={lens_id}, lens_result_id={lens_result.id}")
            return lens_result

        except Exception as e:
            sanitized_message = sanitize_error_message(e)

            # Mark as failed with sanitized error
            lens_result.status = LensResultStatus.FAILED
            lens_result.error_message = sanitized_message
            lens_result.completed_at = datetime.now()
            db.flush()

            # Log sanitized message for standard logs
            logger.error(
                "Lens execution failed: session_id=%s, lens_id=%s, error=%s",
                session_id,
                lens_id,
                sanitized_message,
            )
            # Secure log with full stack trace for debugging if needed
            logger.debug(
                "Full error details for session_id=%s, lens_id=%s (secure)",
                session_id,
                lens_id,
                exc_info=e,
            )

            # Re-raise for caller to handle
            raise

    def execute_all_lenses(
        self,
        db: Session,
        session_id: int,
        active_only: bool = True
    ) -> list[LensResult]:
        """
        Execute all applicable lenses on a session.

        Args:
            db: Database session
            session_id: ID of the InterviewSession to analyze
            active_only: If True, only execute active lenses

        Returns:
            List of LensResult objects
        """
        # Get session
        session = db.get(InterviewSession, session_id)
        if not session:
            raise ValueError(f"InterviewSession {session_id} not found")

        # Get all lenses for this organization
        from sqlalchemy import select
        query = select(Lens).where(Lens.organization_id == session.organization_id)

        if active_only:
            query = query.where(Lens.active == True)

        lenses = db.execute(query).scalars().all()

        # Execute each lens
        results = []
        for lens in lenses:
            try:
                result = self.execute_lens(db, session_id, lens.id)
                results.append(result)
            except Exception as e:
                logger.error(f"Error executing lens {lens.id} ({lens.name}): {e}")
                # Continue with other lenses
                continue

        return results

    def _parse_llm_response(
        self,
        response_text: str,
        lens: Lens
    ) -> list[Dict[str, Any]]:
        """
        Parse and validate LLM response.

        Args:
            response_text: Raw response from LLM
            lens: Lens configuration for validation

        Returns:
            List of criterion result dictionaries

        Raises:
            ValueError: If response is malformed or invalid
        """
        try:
            # Try to parse as JSON
            # Handle case where LLM wraps JSON in markdown code blocks
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                # Extract JSON from code block
                lines = clean_text.split("\n")
                # Remove first line (```json or ```) and last line (```)
                clean_text = "\n".join(lines[1:-1])

            parsed = json.loads(clean_text)

            # Validate structure
            if "criteria_results" not in parsed:
                raise ValueError("Response missing 'criteria_results' field")

            criteria_results = parsed["criteria_results"]
            if not isinstance(criteria_results, list):
                raise ValueError("'criteria_results' must be a list")

            # Validate each criterion result
            expected_criteria = {c["name"] for c in lens.config.get("criteria", [])}
            found_criteria = set()

            for i, result in enumerate(criteria_results):
                # Check required fields
                if "criterion" not in result:
                    raise ValueError(f"Result {i} missing 'criterion' field")

                criterion_name = result["criterion"]
                found_criteria.add(criterion_name)

                # Validate criterion name matches configuration
                if criterion_name not in expected_criteria:
                    logger.warning(f"Unexpected criterion '{criterion_name}' in response")

                # Validate score is numeric if present
                if "score" in result:
                    try:
                        float(result["score"])
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid score for criterion '{criterion_name}': {result['score']}")
                        result["score"] = None

            # Warn if any expected criteria are missing
            missing = expected_criteria - found_criteria
            if missing:
                logger.warning(f"LLM response missing criteria: {missing}")

            return criteria_results

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")

    def _get_provider_name(self) -> str:
        """Get the provider name from the LLM client."""
        client_class = self.llm_client.__class__.__name__
        if "OpenAI" in client_class:
            return "openai"
        elif "Anthropic" in client_class:
            return "anthropic"
        elif "Mock" in client_class:
            return "mock"
        else:
            return "unknown"


def execute_lenses_for_session(
    db: Session,
    session_id: int,
    llm_client: LLMClient,
    model: str = "gpt-4",
    temperature: float = 0.3
) -> list[LensResult]:
    """
    Convenience function to execute all lenses for a session.

    Args:
        db: Database session
        session_id: ID of the InterviewSession
        llm_client: LLM client for making API calls
        model: Model to use
        temperature: Temperature for LLM calls

    Returns:
        List of LensResult objects
    """
    executor = LensExecutor(llm_client, model, temperature)
    return executor.execute_all_lenses(db, session_id, active_only=True)


# ==============================================================================
# Public API
# ==============================================================================

__all__ = [
    "LensExecutor",
    "execute_lenses_for_session",
]

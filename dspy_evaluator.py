"""
DSPy-based interview answer evaluator.

This module provides a drop-in replacement for EvaluatorAgent that uses
DSPy's optimized prompts for semantic keypoint matching instead of
brittle substring matching.

Usage:
    from dspy_evaluator import DSPyEvaluatorAgent

    evaluator = DSPyEvaluatorAgent()
    result = evaluator.evaluate(question, answer)
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    dspy = None

from models import Question, EvaluationResult, KeypointCoverage

logger = logging.getLogger(__name__)


# =============================================================================
# DSPy Signature Definition
# =============================================================================

if DSPY_AVAILABLE:
    class KeypointEvaluation(dspy.Signature):
        """Evaluate interview answer coverage of expected keypoints.

        Given an interview question, candidate answer, and expected keypoints,
        determine which keypoints are covered (semantically, not just literally)
        and provide a score and feedback.
        """

        # Inputs
        question_text: str = dspy.InputField(
            desc="The interview question that was asked"
        )
        answer: str = dspy.InputField(
            desc="The candidate's answer to evaluate"
        )
        keypoints: list[str] = dspy.InputField(
            desc="List of expected concepts that should appear in a good answer"
        )
        difficulty: str = dspy.InputField(
            desc="Question difficulty: Easy, Medium, or Hard"
        )

        # Outputs
        covered_keypoints: list[str] = dspy.OutputField(
            desc="Keypoints the answer addresses (semantic match, not just literal)"
        )
        missed_keypoints: list[str] = dspy.OutputField(
            desc="Keypoints not addressed in the answer"
        )
        score: int = dspy.OutputField(
            desc="Score from 0-100 based on keypoint coverage and answer quality"
        )
        mastery_label: str = dspy.OutputField(
            desc="Mastery level: 'strong' (80-100), 'mixed' (50-79), or 'weak' (0-49)"
        )
        feedback: str = dspy.OutputField(
            desc="Brief, specific feedback on the answer"
        )
        follow_up: str = dspy.OutputField(
            desc="Follow-up question to probe gaps (empty string if score >= 80)"
        )
else:
    KeypointEvaluation = None


# =============================================================================
# DSPy Evaluator Agent
# =============================================================================

class DSPyEvaluatorAgent:
    """
    Interview answer evaluator using DSPy for semantic keypoint matching.

    This is a drop-in replacement for EvaluatorAgent that:
    - Recognizes paraphrased concepts (not just literal keywords)
    - Provides more nuanced feedback
    - Generates targeted follow-up questions
    - Can be optimized using DSPy's BootstrapFewShot

    Args:
        model: LLM model to use (default: gpt-4o-mini)
        compiled_path: Path to saved compiled module (optional)
        temperature: LLM temperature (default: 0.0 for consistency)
        api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        compiled_path: Optional[str] = None,
        temperature: float = 0.0,
        api_key: Optional[str] = None,
    ):
        if not DSPY_AVAILABLE:
            raise ImportError(
                "dspy-ai is required for DSPyEvaluatorAgent. "
                "Install with: pip install dspy-ai"
            )

        self.model = model
        self.temperature = temperature
        self.compiled_path = compiled_path

        # Configure DSPy LM
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Try Anthropic
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_key and "claude" in model.lower():
                lm = dspy.LM(model, api_key=anthropic_key, temperature=temperature)
            else:
                raise ValueError(
                    "No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY."
                )
        else:
            lm = dspy.LM(model, api_key=api_key, temperature=temperature)

        dspy.configure(lm=lm)

        # Create evaluator module
        self.evaluator = dspy.ChainOfThought(KeypointEvaluation)

        # Load compiled module if available
        self._load_compiled_if_exists()

    def _load_compiled_if_exists(self) -> bool:
        """
        Load a pre-compiled (optimized) module if it exists.

        Returns:
            True if compiled module was loaded, False otherwise
        """
        if self.compiled_path is None:
            # Try default path
            default_path = Path(__file__).parent / "compiled_evaluator.json"
            if default_path.exists():
                self.compiled_path = str(default_path)

        if self.compiled_path and Path(self.compiled_path).exists():
            try:
                self.evaluator.load(self.compiled_path)
                logger.info(f"Loaded compiled DSPy module from {self.compiled_path}")
                return True
            except Exception as e:
                logger.warning(f"Failed to load compiled module: {e}")
                return False
        return False

    def evaluate(self, question: Question, answer: str) -> EvaluationResult:
        """
        Evaluate a candidate's answer to a question.

        This method has the same signature as EvaluatorAgent.evaluate()
        for drop-in compatibility.

        Args:
            question: The Question being answered
            answer: The candidate's answer text

        Returns:
            EvaluationResult with score, feedback, and keypoint coverage
        """
        # Handle empty/whitespace answers
        if not answer or not answer.strip():
            return self._empty_answer_result(question, answer)

        try:
            # Call DSPy evaluator
            result = self.evaluator(
                question_text=question.text,
                answer=answer.strip(),
                keypoints=question.keypoints,
                difficulty=question.difficulty,
            )

            return self._to_evaluation_result(question, answer, result)

        except Exception as e:
            logger.error(f"DSPy evaluation failed: {e}", exc_info=True)
            return self._error_fallback(question, answer, str(e))

    def _to_evaluation_result(
        self,
        question: Question,
        answer: str,
        result,
    ) -> EvaluationResult:
        """
        Convert DSPy prediction to EvaluationResult.

        Args:
            question: Original question
            answer: Candidate's answer
            result: DSPy prediction object

        Returns:
            EvaluationResult instance
        """
        # Extract and normalize values
        covered = self._normalize_list(result.covered_keypoints)
        missed = self._normalize_list(result.missed_keypoints)
        score = self._normalize_score(result.score)
        mastery = self._normalize_mastery(result.mastery_label, score)
        feedback = str(result.feedback or "").strip()
        follow_up = str(result.follow_up or "").strip()

        # Build keypoint coverage list
        coverage = []
        covered_set = {kp.lower() for kp in covered}

        for keypoint in question.keypoints:
            is_covered = keypoint.lower() in covered_set
            coverage.append(KeypointCoverage(
                keypoint=keypoint,
                covered=is_covered,
                evidence=None  # DSPy doesn't extract evidence snippets
            ))

        # Clear follow-up if score is high
        if score >= 80:
            follow_up = None

        return EvaluationResult(
            question_id=question.id,
            raw_answer=answer,
            score_0_100=score,
            mastery_label=mastery,
            keypoints_coverage=coverage,
            short_feedback=feedback or f"Score: {score}/100",
            suggested_followup=follow_up if follow_up else None,
        )

    def _normalize_list(self, value) -> list[str]:
        """Normalize DSPy output to list of strings."""
        if value is None:
            return []
        if isinstance(value, str):
            # Try parsing as JSON array
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except json.JSONDecodeError:
                pass
            # Split by comma if it looks like a list
            if "," in value:
                return [x.strip() for x in value.split(",") if x.strip()]
            return [value] if value.strip() else []
        if isinstance(value, list):
            return [str(x) for x in value]
        return []

    def _normalize_score(self, value) -> int:
        """Normalize score to 0-100 integer."""
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return max(0, min(100, int(value)))
        if isinstance(value, str):
            try:
                # Handle "85%" or "85"
                clean = value.replace("%", "").strip()
                return max(0, min(100, int(float(clean))))
            except ValueError:
                return 0
        return 0

    def _normalize_mastery(self, value, score: int) -> str:
        """Normalize mastery label, using score as fallback."""
        if value:
            value_lower = str(value).lower().strip()
            if value_lower in ("strong", "excellent", "good"):
                return "strong"
            if value_lower in ("mixed", "partial", "moderate"):
                return "mixed"
            if value_lower in ("weak", "poor", "insufficient"):
                return "weak"

        # Derive from score
        if score >= 80:
            return "strong"
        elif score >= 50:
            return "mixed"
        else:
            return "weak"

    def _empty_answer_result(
        self,
        question: Question,
        answer: str,
    ) -> EvaluationResult:
        """Generate result for empty/blank answer."""
        coverage = [
            KeypointCoverage(keypoint=kp, covered=False, evidence=None)
            for kp in question.keypoints
        ]

        return EvaluationResult(
            question_id=question.id,
            raw_answer=answer,
            score_0_100=0,
            mastery_label="weak",
            keypoints_coverage=coverage,
            short_feedback="No answer provided.",
            suggested_followup=f"Can you explain {question.keypoints[0] if question.keypoints else 'this concept'}?",
        )

    def _error_fallback(
        self,
        question: Question,
        answer: str,
        error_message: str,
    ) -> EvaluationResult:
        """Generate fallback result when evaluation fails."""
        coverage = [
            KeypointCoverage(keypoint=kp, covered=False, evidence=None)
            for kp in question.keypoints
        ]

        return EvaluationResult(
            question_id=question.id,
            raw_answer=answer,
            score_0_100=0,
            mastery_label="weak",
            keypoints_coverage=coverage,
            short_feedback="Evaluation failed. Please try again.",
            suggested_followup=None,
            error="DSPy evaluation error",
            error_details={"message": error_message},
        )

    def save_compiled(self, path: str) -> None:
        """
        Save the current evaluator module (for use after optimization).

        Args:
            path: File path to save the compiled module
        """
        self.evaluator.save(path)
        logger.info(f"Saved compiled DSPy module to {path}")


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    "DSPyEvaluatorAgent",
    "KeypointEvaluation",
    "DSPY_AVAILABLE",
]

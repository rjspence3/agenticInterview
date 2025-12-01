"""
Data models for the Agentic Interview System.

This module contains pure data classes with no business logic.
All models use dataclasses for clean, typed data structures.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Question:
    """
    Represents a single interview question.

    Attributes:
        id: Unique identifier for the question
        text: The actual question text
        competency: Area being tested (e.g., "Python", "System Design")
        difficulty: Difficulty level (e.g., "Easy", "Medium", "Hard")
        keypoints: List of ground-truth concepts that should appear in a good answer
    """
    id: int
    text: str
    competency: str
    difficulty: str
    keypoints: list[str]


@dataclass
class KeypointCoverage:
    """
    Tracks whether a specific keypoint was covered in the candidate's answer.

    Attributes:
        keypoint: The keypoint text being evaluated
        covered: Whether this keypoint was found in the answer
        evidence: Optional excerpt from answer showing where keypoint was covered
    """
    keypoint: str
    covered: bool
    evidence: Optional[str] = None


@dataclass
class EvaluationResult:
    """
    Result of evaluating a candidate's answer to a question.

    Attributes:
        question_id: ID of the question that was answered
        raw_answer: The candidate's submitted answer text
        score_0_100: Numeric score from 0-100
        mastery_label: Qualitative assessment ("strong", "mixed", "weak")
        keypoints_coverage: Detailed coverage for each keypoint
        short_feedback: Brief feedback explaining the score
        suggested_followup: Optional suggestion for follow-up questions
        error: Optional error message if evaluation failed
    """
    question_id: int
    raw_answer: str
    score_0_100: int
    mastery_label: str
    keypoints_coverage: list[KeypointCoverage]
    short_feedback: str
    suggested_followup: Optional[str] = None
    error: Optional[str] = None


@dataclass
class InterviewState:
    """
    Tracks the state of an ongoing interview.

    Attributes:
        current_index: Index of the current question (0-based)
        finished: Whether the interview is complete
        evaluations: Map of question_id to EvaluationResult for answered questions
    """
    current_index: int = 0
    finished: bool = False
    evaluations: dict[int, EvaluationResult] = field(default_factory=dict)


# ==============================================================================
# Public API
# ==============================================================================

__all__ = [
    "Question",
    "KeypointCoverage",
    "EvaluationResult",
    "InterviewState",
]

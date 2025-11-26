"""
Agent implementations for the Agentic Interview System.

This module contains the core business logic split across three agents:
- QuestionsAgent: Manages the question bank
- EvaluatorAgent: Evaluates answers against ground truth (heuristic for MVP)
- OrchestratorAgent: Coordinates the interview flow

No Streamlit dependencies - these are pure Python classes.
"""

from typing import Optional
from models import Question, EvaluationResult, KeypointCoverage, InterviewState


class QuestionsAgent:
    """
    Manages the question bank and serves questions during the interview.
    """

    def __init__(self, questions: list[Question]):
        """
        Initialize with a list of questions.

        Args:
            questions: List of Question objects to use in interviews
        """
        self.questions = questions

    def get_next_question(self, current_index: int) -> Optional[Question]:
        """
        Get the question at the specified index.

        Args:
            current_index: 0-based index of the question to retrieve

        Returns:
            Question object if index is valid, None otherwise
        """
        if 0 <= current_index < len(self.questions):
            return self.questions[current_index]
        return None

    def count(self) -> int:
        """Return the total number of questions."""
        return len(self.questions)


class EvaluatorAgent:
    """
    Evaluates candidate answers against question keypoints.

    MVP Implementation: Uses simple heuristic (substring matching).
    Future: Will be replaced with LLM-based evaluation.
    """

    def evaluate(self, question: Question, answer: str) -> EvaluationResult:
        """
        Evaluate a candidate's answer to a question.

        Args:
            question: The Question being answered
            answer: The candidate's answer text

        Returns:
            EvaluationResult with score, feedback, and keypoint coverage
        """
        # TODO: Replace this heuristic with LLM-based evaluation
        # Future LLM implementation should:
        # - Use few-shot prompting with examples
        # - Consider semantic similarity, not just keyword matching
        # - Generate more nuanced feedback
        # - Suggest meaningful follow-up questions

        # Normalize answer for matching
        answer_lower = answer.lower().strip()

        # Evaluate each keypoint
        coverage: list[KeypointCoverage] = []
        covered_count = 0

        for keypoint in question.keypoints:
            keypoint_lower = keypoint.lower()
            is_covered = keypoint_lower in answer_lower

            # Find evidence if covered
            evidence = None
            if is_covered:
                covered_count += 1
                # Extract a snippet containing the keypoint
                idx = answer_lower.find(keypoint_lower)
                start = max(0, idx - 20)
                end = min(len(answer), idx + len(keypoint) + 20)
                evidence = f"...{answer[start:end]}..."

            coverage.append(KeypointCoverage(
                keypoint=keypoint,
                covered=is_covered,
                evidence=evidence
            ))

        # Calculate score
        total_keypoints = len(question.keypoints)
        if total_keypoints == 0:
            score = 100  # No keypoints means any answer is fine
        else:
            score = int((covered_count / total_keypoints) * 100)

        # Determine mastery label
        if score >= 80:
            mastery_label = "strong"
        elif score >= 50:
            mastery_label = "mixed"
        else:
            mastery_label = "weak"

        # Generate feedback
        if covered_count == total_keypoints:
            short_feedback = f"Excellent! Covered all {total_keypoints} keypoints."
        elif covered_count > 0:
            missed = total_keypoints - covered_count
            short_feedback = (
                f"Covered {covered_count}/{total_keypoints} keypoints. "
                f"Missing: {', '.join([kp.keypoint for kp in coverage if not kp.covered])}."
            )
        else:
            short_feedback = f"Did not cover any of the {total_keypoints} expected keypoints."

        # TODO: LLM would generate personalized follow-up questions
        suggested_followup = None
        if score < 80 and covered_count > 0:
            missed_points = [kp.keypoint for kp in coverage if not kp.covered]
            if missed_points:
                suggested_followup = f"Can you elaborate on: {missed_points[0]}?"

        return EvaluationResult(
            question_id=question.id,
            raw_answer=answer,
            score_0_100=score,
            mastery_label=mastery_label,
            keypoints_coverage=coverage,
            short_feedback=short_feedback,
            suggested_followup=suggested_followup
        )


class OrchestratorAgent:
    """
    Orchestrates the interview flow by coordinating QuestionsAgent and EvaluatorAgent.
    """

    def __init__(self, questions_agent: QuestionsAgent, evaluator_agent: EvaluatorAgent):
        """
        Initialize with agent dependencies.

        Args:
            questions_agent: Agent managing the question bank
            evaluator_agent: Agent evaluating answers
        """
        self.questions_agent = questions_agent
        self.evaluator_agent = evaluator_agent

    def step(self, state: InterviewState, answer: Optional[str]) -> InterviewState:
        """
        Process one step of the interview.

        If an answer is provided, evaluates it and advances to the next question.
        Marks the interview as finished when all questions are answered.

        Args:
            state: Current interview state
            answer: Candidate's answer to current question (None to just check state)

        Returns:
            Updated InterviewState
        """
        # If already finished, return unchanged
        if state.finished:
            return state

        # If answer provided, evaluate it
        if answer and answer.strip():
            current_question = self.questions_agent.get_next_question(state.current_index)

            if current_question:
                # Evaluate the answer
                evaluation = self.evaluator_agent.evaluate(current_question, answer)

                # Store evaluation
                state.evaluations[current_question.id] = evaluation

                # Advance to next question
                state.current_index += 1

        # Check if interview is complete
        if state.current_index >= self.questions_agent.count():
            state.finished = True

        return state

    def generate_summary(self, state: InterviewState) -> str:
        """
        Generate a summary of the completed interview.

        Args:
            state: Completed interview state

        Returns:
            Summary string with overall performance assessment
        """
        if not state.evaluations:
            return "No questions were answered."

        # Calculate overall score
        scores = [eval_result.score_0_100 for eval_result in state.evaluations.values()]
        avg_score = sum(scores) / len(scores)

        # Count mastery levels
        mastery_counts = {"strong": 0, "mixed": 0, "weak": 0}
        for eval_result in state.evaluations.values():
            mastery_counts[eval_result.mastery_label] += 1

        # Build summary
        summary_parts = [
            f"Interview Complete! Overall Score: {avg_score:.1f}/100",
            f"",
            f"Performance Breakdown:",
            f"  Strong: {mastery_counts['strong']} questions",
            f"  Mixed:  {mastery_counts['mixed']} questions",
            f"  Weak:   {mastery_counts['weak']} questions",
        ]

        # Overall assessment
        if avg_score >= 80:
            assessment = "Excellent performance across most areas."
        elif avg_score >= 60:
            assessment = "Solid performance with some areas for improvement."
        elif avg_score >= 40:
            assessment = "Demonstrated basic understanding but needs more depth."
        else:
            assessment = "Significant gaps in key concepts."

        summary_parts.append(f"\n{assessment}")

        return "\n".join(summary_parts)


# ==============================================================================
# Public API
# ==============================================================================

__all__ = [
    "QuestionsAgent",
    "EvaluatorAgent",
    "OrchestratorAgent",
]

"""
LLM-Powered Evaluator Agent

Uses Large Language Models (OpenAI, Anthropic, etc.) to semantically evaluate
candidate answers against ground-truth keypoints.

Drop-in replacement for the heuristic EvaluatorAgent with same interface.
"""

import json

from logging_config import get_logger
from models import EvaluationResult, KeypointCoverage, Question
from llm_client import LLMClient


# ==============================================================================
# Prompt Template
# ==============================================================================

EVALUATION_PROMPT_TEMPLATE = """You are an expert technical interviewer evaluating a candidate's answer.

QUESTION:
{question_text}

COMPETENCY: {competency}
DIFFICULTY: {difficulty}

GROUND TRUTH KEYPOINTS (the candidate should cover these):
{keypoints_numbered}

CANDIDATE'S ANSWER:
{candidate_answer}

TASK:
1. For each keypoint, determine if it was adequately covered in the answer.
   - Mark as "covered" if the concept is present (even if phrased differently)
   - Provide a brief evidence snippet showing where it was covered (or note if missing)

2. Assign an overall score from 0-100 based on:
   - Keypoint coverage (primary factor: each keypoint ≈ {points_per_keypoint} points)
   - Depth of explanation (bonus up to 10 points)
   - Accuracy of information (deduct for errors)
   - Clarity of communication (minor factor)

3. Classify mastery level:
   - "strong": 80-100 points (comprehensive understanding)
   - "mixed": 50-79 points (partial understanding, gaps present)
   - "weak": 0-49 points (significant gaps or misconceptions)

4. Generate short feedback (2-3 sentences) explaining the score and what was strong/weak.

5. If score < 80 and some keypoints were covered, suggest ONE follow-up question to probe the missing concepts.
   If score >= 80, leave suggested_followup empty.

OUTPUT FORMAT (strict JSON, no other text):
{{
  "keypoints_coverage": [
    {{"keypoint": "First keypoint text", "covered": true, "evidence": "Quote showing where addressed"}},
    {{"keypoint": "Second keypoint text", "covered": false, "evidence": "Not mentioned"}}
  ],
  "score": 75,
  "mastery_label": "mixed",
  "feedback": "Answer covers X and Y well but misses Z. Explanation of X was thorough.",
  "suggested_followup": "Can you explain how Z relates to X?"
}}

EXAMPLE 1 - Strong Answer:
Question: "What is recursion?"
Keypoints: ["base case", "recursive case", "stack usage"]
Answer: "Recursion is when a function calls itself. You need a base case to stop, and a recursive case that moves toward it. Each call uses stack memory."

Output:
{{
  "keypoints_coverage": [
    {{"keypoint": "base case", "covered": true, "evidence": "mentioned 'base case to stop'"}},
    {{"keypoint": "recursive case", "covered": true, "evidence": "described 'recursive case that moves toward it'"}},
    {{"keypoint": "stack usage", "covered": true, "evidence": "stated 'uses stack memory'"}}
  ],
  "score": 95,
  "mastery_label": "strong",
  "feedback": "Excellent concise answer covering all key concepts of recursion with correct terminology.",
  "suggested_followup": ""
}}

EXAMPLE 2 - Partial Answer:
Question: "What is recursion?"
Keypoints: ["base case", "recursive case", "stack usage"]
Answer: "A function that calls itself."

Output:
{{
  "keypoints_coverage": [
    {{"keypoint": "base case", "covered": false, "evidence": "Not mentioned"}},
    {{"keypoint": "recursive case", "covered": true, "evidence": "implicit in 'calls itself'"}},
    {{"keypoint": "stack usage", "covered": false, "evidence": "Not mentioned"}}
  ],
  "score": 35,
  "mastery_label": "weak",
  "feedback": "Very minimal answer. Identifies self-calling but misses critical concepts of base case and stack implications.",
  "suggested_followup": "What prevents a recursive function from running forever?"
}}

Now evaluate the candidate's answer above and output ONLY the JSON.
"""


# ==============================================================================
# LLM Evaluator Agent
# ==============================================================================

class LLMEvaluatorAgent:
    """
    LLM-powered evaluator that semantically analyzes candidate answers.

    Drop-in replacement for EvaluatorAgent with same interface.
    Uses LLM to understand answer quality beyond keyword matching.

    Design:
    - Same public interface as EvaluatorAgent (evaluate method)
    - Uses injected LLMClient for testability
    - Robust error handling with fallback responses
    - Detailed logging for debugging
    """

    def __init__(self, llm_client: LLMClient, model: str, temperature: float):
        """
        Initialize LLM evaluator.

        Args:
            llm_client: LLMClient instance (OpenAI, Anthropic, or Mock)
            model: Model identifier (e.g., "gpt-4", "claude-3-5-sonnet-20241022")
            temperature: 0.0-1.0, controls randomness (recommend 0.2-0.4 for consistency)
        """
        self.llm_client = llm_client
        self.model = model
        self.temperature = temperature
        self.logger = get_logger(__name__)

    def evaluate(self, question: Question, answer: str) -> EvaluationResult:
        """
        Evaluate candidate answer using LLM.

        Same interface as EvaluatorAgent.evaluate().

        Args:
            question: Question object with keypoints
            answer: Candidate's answer text

        Returns:
            EvaluationResult with score, feedback, and keypoint coverage
        """
        self.logger.info(
            "Starting LLM evaluation",
            extra={"question_id": question.id, "model": self.model},
        )

        # Step 1: Build prompt from template
        prompt = self._build_prompt(question, answer)

        # Step 2: Call LLM
        try:
            response_text = self.llm_client.call_llm(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature
            )
        except Exception as e:
            # LLM call failed, return error fallback
            self.logger.error(
                "LLM call failed",
                extra={"question_id": question.id, "model": self.model, "error": str(e)},
            )
            return self._error_fallback(question, answer, str(e))

        # Step 3: Parse JSON response
        try:
            result = self._parse_response(response_text, question, answer)
            self.logger.info(
                "LLM evaluation completed",
                extra={"question_id": question.id, "model": self.model},
            )
            return result
        except Exception as e:
            # Parsing failed, return error fallback
            self.logger.error(
                "Response parsing failed",
                extra={
                    "question_id": question.id,
                    "model": self.model,
                    "error": str(e),
                    "raw_response": response_text,
                },
            )
            return self._error_fallback(question, answer, f"Parse error: {e}")

    def _build_prompt(self, question: Question, answer: str) -> str:
        """
        Build evaluation prompt from template.

        Args:
            question: Question with keypoints
            answer: Candidate's answer

        Returns:
            Formatted prompt string
        """
        # Format keypoints as numbered list
        keypoints_numbered = "\n".join(
            f"{i+1}. {kp}" for i, kp in enumerate(question.keypoints)
        )

        # Calculate points per keypoint (for guidance in prompt)
        points_per_keypoint = 100 // len(question.keypoints) if question.keypoints else 100

        # Handle empty answer
        candidate_answer = answer.strip() if answer.strip() else "[Empty answer - no response provided]"

        # Fill template
        prompt = EVALUATION_PROMPT_TEMPLATE.format(
            question_text=question.text,
            competency=question.competency,
            difficulty=question.difficulty,
            keypoints_numbered=keypoints_numbered,
            points_per_keypoint=points_per_keypoint,
            candidate_answer=candidate_answer
        )

        return prompt

    def _parse_response(self, response: str, question: Question, answer: str) -> EvaluationResult:
        """
        Parse LLM JSON response into EvaluationResult.

        Args:
            response: Raw text response from LLM
            question: Original question
            answer: Original answer

        Returns:
            EvaluationResult object

        Raises:
            ValueError: If JSON is malformed or missing required fields
            json.JSONDecodeError: If response is not valid JSON
        """
        # Extract JSON from response (LLM may add extra text)
        json_start = response.find('{')
        json_end = response.rfind('}') + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in LLM response")

        json_str = response[json_start:json_end]

        # Parse JSON
        data = json.loads(json_str)

        # Validate required fields
        required_fields = ["keypoints_coverage", "score", "mastery_label", "feedback"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Build KeypointCoverage list
        coverage = []
        for item in data["keypoints_coverage"]:
            coverage.append(KeypointCoverage(
                keypoint=item["keypoint"],
                covered=item["covered"],
                evidence=item.get("evidence", "")
            ))

        # Validate mastery label
        mastery_label = data["mastery_label"]
        if mastery_label not in ["strong", "mixed", "weak"]:
            self.logger.warning(
                "Invalid mastery label; defaulting to 'mixed'",
                extra={"question_id": question.id, "model": self.model, "mastery_label": mastery_label},
            )
            mastery_label = "mixed"

        # Clamp score to 0-100
        score = max(0, min(100, data["score"]))

        # Build and return EvaluationResult
        return EvaluationResult(
            question_id=question.id,
            raw_answer=answer,
            score_0_100=score,
            mastery_label=mastery_label,
            keypoints_coverage=coverage,
            short_feedback=data["feedback"],
            suggested_followup=data.get("suggested_followup", ""),
            error=None,
        )

    def _error_fallback(self, question: Question, answer: str, error: str) -> EvaluationResult:
        """
        Return a safe error result if LLM evaluation fails.

        This ensures the system continues working even if LLM is unavailable.

        Args:
            question: Original question
            answer: Original answer
            error: Error message

        Returns:
            EvaluationResult with error information
        """
        # Create coverage marking all keypoints as not evaluated
        coverage = [
            KeypointCoverage(
                keypoint=kp,
                covered=False,
                evidence="[Evaluation error - unable to assess]"
            )
            for kp in question.keypoints
        ]

        return EvaluationResult(
            question_id=question.id,
            raw_answer=answer,
            score_0_100=0,
            mastery_label="weak",
            keypoints_coverage=coverage,
            short_feedback=f"Unable to evaluate answer due to error: {error}",
            suggested_followup="Please try again or use heuristic evaluator.",
            error=error,
        )


# ==============================================================================
# Module Test
# ==============================================================================

if __name__ == "__main__":
    # Test with MockLLMClient
    from llm_client import MockLLMClient

    print("Testing LLMEvaluatorAgent with MockLLMClient...")

    # Create test question
    question = Question(
        id="test-1",
        text="What is recursion in programming?",
        competency="Python",
        difficulty="Medium",
        keypoints=["base case", "recursive case", "stack usage"]
    )

    # Create evaluator with mock client
    mock_client = MockLLMClient()
    evaluator = LLMEvaluatorAgent(mock_client, "mock", 0.3)

    # Test cases
    test_cases = [
        ("Perfect answer", "Recursion is when a function calls itself. You need a base case to stop and recursive case to continue. Each call uses the call stack."),
        ("Partial answer", "A function that calls itself with a base case."),
        ("Weak answer", "It's like a loop."),
        ("Empty answer", "")
    ]

    for name, answer_text in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {name}")
        print(f"Answer: {answer_text[:50]}..." if len(answer_text) > 50 else f"Answer: {answer_text}")
        print(f"{'='*60}")

        result = evaluator.evaluate(question, answer_text)

        print(f"Score: {result.score_0_100}/100")
        print(f"Mastery: {result.mastery_label}")
        print(f"Feedback: {result.short_feedback}")
        print(f"Covered: {sum(1 for kc in result.keypoints_coverage if kc.covered)}/{len(result.keypoints_coverage)} keypoints")

        if result.suggested_followup:
            print(f"Follow-up: {result.suggested_followup}")

    print("\n" + "="*60)
    print("LLMEvaluatorAgent tests complete!")


# ==============================================================================
# Public API
# ==============================================================================

__all__ = [
    "LLMEvaluatorAgent",
    "EVALUATION_PROMPT_TEMPLATE",
]

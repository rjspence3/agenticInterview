"""
Unit tests for LLM Evaluator Agent.

Tests the LLMEvaluatorAgent using MockLLMClient (no real API calls).
Verifies prompt construction, response parsing, error handling, and interface compatibility.
"""

import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import EvaluationResult, KeypointCoverage, Question
from llm_evaluator import LLMEvaluatorAgent
from llm_client import MockLLMClient
import json


def test_response_parsing_strips_markdown_and_trailing_text():
    """JSON wrapped in fences and extra text should be normalized before parsing."""
    question = Question(
        id="test-fence",
        text="Explain lists",
        competency="Python",
        difficulty="Easy",
        keypoints=["ordered", "mutable"],
    )

    evaluator = LLMEvaluatorAgent(MockLLMClient(), "mock", 0.3)

    fenced_response = """
Here you go:
```json
{
  "keypoints_coverage": [
    {"keypoint": "ordered", "covered": true, "evidence": "mentioned ordering"},
    {"keypoint": "mutable", "covered": false, "evidence": "Not mentioned"}
  ],
  "score": 72,
  "mastery_label": "mixed",
  "feedback": "Good but needs mutability",
  "suggested_followup": "Can you explain mutability?"
}
```
Thanks!
"""

    result = evaluator._parse_response(fenced_response, question, "answer")

    assert result.score_0_100 == 72
    assert result.mastery_label == "mixed"
    assert len(result.keypoints_coverage) == 2
    assert result.keypoints_coverage[0].covered is True


def test_prompt_construction():
    """Test that prompts include all question fields."""
    print("\n=== Test: Prompt Construction ===")

    question = Question(
        id="test-1",
        text="What is recursion?",
        competency="Python",
        difficulty="Medium",
        keypoints=["base case", "recursive case", "stack usage"]
    )

    evaluator = LLMEvaluatorAgent(MockLLMClient(), "mock", 0.3)

    # Build prompt
    prompt = evaluator._build_prompt(question, "test answer")

    # Verify all fields present
    assert "What is recursion?" in prompt, "Question text missing from prompt"
    assert "Python" in prompt, "Competency missing from prompt"
    assert "Medium" in prompt, "Difficulty missing from prompt"
    assert "base case" in prompt, "Keypoint 1 missing from prompt"
    assert "recursive case" in prompt, "Keypoint 2 missing from prompt"
    assert "stack usage" in prompt, "Keypoint 3 missing from prompt"
    assert "test answer" in prompt, "Answer missing from prompt"

    print("✓ Prompt contains all required fields")


def test_response_parsing_valid_json():
    """Test parsing of well-formed LLM response."""
    print("\n=== Test: Valid JSON Parsing ===")

    question = Question(
        id="test-2",
        text="Explain lists",
        competency="Python",
        difficulty="Easy",
        keypoints=["ordered", "mutable"]
    )

    evaluator = LLMEvaluatorAgent(MockLLMClient(), "mock", 0.3)

    # Mock valid JSON response
    valid_response = json.dumps({
        "keypoints_coverage": [
            {"keypoint": "ordered", "covered": True, "evidence": "mentioned ordering"},
            {"keypoint": "mutable", "covered": False, "evidence": "Not mentioned"}
        ],
        "score": 50,
        "mastery_label": "mixed",
        "feedback": "Partial understanding",
        "suggested_followup": "Can you explain mutability?"
    })

    # Parse response
    result = evaluator._parse_response(valid_response, question, "test answer")

    # Verify parsing
    assert isinstance(result, EvaluationResult), "Should return EvaluationResult"
    assert result.question_id == "test-2", "Question ID mismatch"
    assert result.score_0_100 == 50, "Score mismatch"
    assert result.mastery_label == "mixed", "Mastery label mismatch"
    assert "Partial understanding" in result.short_feedback, "Feedback mismatch"
    assert len(result.keypoints_coverage) == 2, "Keypoints coverage count mismatch"
    assert result.keypoints_coverage[0].covered == True, "First keypoint should be covered"
    assert result.keypoints_coverage[1].covered == False, "Second keypoint should not be covered"

    print("✓ Valid JSON parsed correctly")


def test_response_parsing_malformed_json():
    """Test graceful handling of bad JSON."""
    print("\n=== Test: Malformed JSON Handling ===")

    question = Question(
        id="test-3",
        text="Test question",
        competency="Testing",
        difficulty="Easy",
        keypoints=["test"]
    )

    evaluator = LLMEvaluatorAgent(MockLLMClient(), "mock", 0.3)

    # Try to parse malformed response
    try:
        result = evaluator._parse_response("This is not JSON", question, "answer")
        # Should use error fallback
        assert result.score_0_100 == 0, "Error fallback should give 0 score"
        assert result.mastery_label == "weak", "Error fallback should give weak mastery"
        print("✓ Malformed JSON handled gracefully (via error fallback)")
    except ValueError:
        # Or it might raise ValueError, which is also acceptable
        print("✓ Malformed JSON raises ValueError (acceptable)")


def test_validation_errors_surface_structured_error(caplog):
    """Validation failures should be logged and returned via structured error details."""
    caplog.set_level(logging.ERROR)

    class InvalidPayloadClient:
        def call_llm(self, *args, **kwargs):
            return json.dumps(
                {
                    "keypoints_coverage": [
                        {"keypoint": "ordered", "covered": "yes"},
                    ],
                    "score": 120,
                    "mastery_label": "excellent",
                    "feedback": ["Not a string"],
                }
            )

    question = Question(
        id="validation-1",
        text="Explain lists",
        competency="Python",
        difficulty="Easy",
        keypoints=["ordered"],
    )

    evaluator = LLMEvaluatorAgent(InvalidPayloadClient(), "mock", 0.3)
    result = evaluator.evaluate(question, "answer")

    assert result.error_details == {
        "code": "parse_error",
        "message": result.error.replace("Parse error: ", ""),
    }
    assert "score must be between 0 and 100" in result.error
    assert any("validation failed" in record.message for record in caplog.records)


def test_llm_call_error_sets_error_and_logs(caplog):
    """Simulate LLM call errors to ensure logging and error field are set."""
    caplog.set_level(logging.ERROR)

    class FailingLLMClient:
        def call_llm(self, *args, **kwargs):
            raise RuntimeError("Synthetic failure")

    question = Question(
        id="error-1",
        text="What is a test?",
        competency="Testing",
        difficulty="Easy",
        keypoints=["definition"],
    )

    evaluator = LLMEvaluatorAgent(FailingLLMClient(), "mock", 0.3)
    result = evaluator.evaluate(question, "answer")

    assert result.error is not None, "Error field should capture failure"
    assert "Synthetic failure" in result.error, "Error message should describe failure"
    assert result.score_0_100 == 0, "Error should return zero score"
    assert any("LLM call failed" in record.message for record in caplog.records), "Error should be logged"
    assert any(getattr(record, "question_id", None) == question.id for record in caplog.records), "Log should include question context"
    assert any(getattr(record, "model", None) == "mock" for record in caplog.records), "Log should include model context"


def test_malformed_json_sets_error_and_logs(caplog):
    """Ensure malformed JSON responses are logged and surfaced via error field."""
    caplog.set_level(logging.ERROR)

    class BadJSONClient:
        def call_llm(self, *args, **kwargs):
            return "not-json"

    question = Question(
        id="error-2",
        text="Another test?",
        competency="Testing",
        difficulty="Medium",
        keypoints=["item"],
    )

    evaluator = LLMEvaluatorAgent(BadJSONClient(), "mock", 0.3)
    result = evaluator.evaluate(question, "answer")

    assert result.error is not None, "Error field should indicate parse failure"
    assert "Parse error" in result.error, "Parse errors should be surfaced in error message"
    assert result.score_0_100 == 0, "Parse errors should return zero score"
    assert any("Response parsing failed" in record.message for record in caplog.records), "Parse error should be logged"
    assert any(getattr(record, "raw_response", None) == "not-json" for record in caplog.records), "Log should include raw response"
    assert any(getattr(record, "question_id", None) == question.id for record in caplog.records), "Log should include question context"
    assert any(getattr(record, "model", None) == "mock" for record in caplog.records), "Log should include model context"


def test_error_fallback():
    """Test error fallback when evaluation fails."""
    print("\n=== Test: Error Fallback ===")

    question = Question(
        id="test-4",
        text="Test question",
        competency="Testing",
        difficulty="Easy",
        keypoints=["concept1", "concept2"]
    )

    evaluator = LLMEvaluatorAgent(MockLLMClient(), "mock", 0.3)

    # Generate error fallback
    result = evaluator._error_fallback(question, "test answer", "Simulated error")

    # Verify fallback
    assert result.question_id == "test-4", "Question ID should match"
    assert result.score_0_100 == 0, "Error fallback should give 0 score"
    assert result.mastery_label == "weak", "Error fallback should give weak mastery"
    assert "error" in result.short_feedback.lower(), "Feedback should mention error"
    assert len(result.keypoints_coverage) == 2, "Should have coverage for all keypoints"
    assert all(not kc.covered for kc in result.keypoints_coverage), "No keypoints should be marked covered"

    print("✓ Error fallback works correctly")


def test_empty_answer():
    """Test evaluation of empty answer."""
    print("\n=== Test: Empty Answer ===")

    question = Question(
        id="test-5",
        text="What is Python?",
        competency="Python",
        difficulty="Easy",
        keypoints=["programming language", "interpreted"]
    )

    evaluator = LLMEvaluatorAgent(MockLLMClient(), "mock", 0.3)

    # Evaluate empty answer
    result = evaluator.evaluate(question, "")

    # Should return valid result
    assert isinstance(result, EvaluationResult), "Should return EvaluationResult"
    assert result.score_0_100 <= 10, "Empty answer should score very low"
    assert result.mastery_label == "weak", "Empty answer should be weak"

    print("✓ Empty answer handled correctly")


def test_mock_client():
    """Test MockLLMClient returns expected format."""
    print("\n=== Test: MockLLMClient Format ===")

    mock_client = MockLLMClient()

    # Create test prompt
    test_prompt = """
QUESTION:
What is recursion?

GROUND TRUTH KEYPOINTS (the candidate should cover these):
1. base case
2. recursive case

CANDIDATE'S ANSWER:
Recursion is when a function calls itself with a base case.
"""

    # Call mock client
    response = mock_client.call_llm(test_prompt, "mock", 0.3)

    # Verify response is valid JSON
    try:
        data = json.loads(response)
        assert "keypoints_coverage" in data, "Missing keypoints_coverage"
        assert "score" in data, "Missing score"
        assert "mastery_label" in data, "Missing mastery_label"
        assert "feedback" in data, "Missing feedback"
        assert "suggested_followup" in data, "Missing suggested_followup"
        print("✓ MockLLMClient returns valid JSON format")
    except json.JSONDecodeError:
        raise AssertionError("MockLLMClient should return valid JSON")


def test_evaluator_interface_compatibility():
    """Test that LLMEvaluatorAgent has same interface as EvaluatorAgent."""
    print("\n=== Test: Interface Compatibility ===")

    from agents import EvaluatorAgent

    # Both should have evaluate method
    assert hasattr(LLMEvaluatorAgent, 'evaluate'), "LLMEvaluatorAgent missing evaluate method"
    assert hasattr(EvaluatorAgent, 'evaluate'), "EvaluatorAgent missing evaluate method"

    # Create instances
    llm_eval = LLMEvaluatorAgent(MockLLMClient(), "mock", 0.3)
    heuristic_eval = EvaluatorAgent()

    # Both should accept same arguments
    question = Question(
        id="test-6",
        text="Test",
        competency="Test",
        difficulty="Easy",
        keypoints=["test"]
    )

    # Both should return EvaluationResult
    llm_result = llm_eval.evaluate(question, "test answer")
    heuristic_result = heuristic_eval.evaluate(question, "test answer")

    assert isinstance(llm_result, EvaluationResult), "LLM evaluator should return EvaluationResult"
    assert isinstance(heuristic_result, EvaluationResult), "Heuristic evaluator should return EvaluationResult"

    print("✓ LLMEvaluatorAgent is interface-compatible with EvaluatorAgent")


def test_full_evaluation_flow():
    """Test complete evaluation flow with MockLLMClient."""
    print("\n=== Test: Full Evaluation Flow ===")

    question = Question(
        id="test-7",
        text="What is recursion in programming?",
        competency="Python",
        difficulty="Medium",
        keypoints=["base case", "recursive case", "stack usage"]
    )

    evaluator = LLMEvaluatorAgent(MockLLMClient(), "mock", 0.3)

    # Test perfect answer (with exact keypoint matches for mock's simple matching)
    perfect_answer = "Recursion is when a function calls itself. You need a base case to stop and a recursive case to continue. It uses stack usage for each call."
    result = evaluator.evaluate(question, perfect_answer)

    assert result.score_0_100 >= 80, f"Perfect answer should score high, got {result.score_0_100}"
    assert result.mastery_label in ["strong", "mixed", "weak"], "Should have valid mastery label"
    assert result.short_feedback, "Should have feedback"

    # Test partial answer
    partial_answer = "A function that calls itself"
    result = evaluator.evaluate(question, partial_answer)

    assert result.score_0_100 < 80, "Partial answer should score lower"

    print("✓ Full evaluation flow works correctly")


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("Running LLM Evaluator Tests")
    print("=" * 60)

    tests = [
        test_prompt_construction,
        test_response_parsing_valid_json,
        test_response_parsing_malformed_json,
        test_error_fallback,
        test_empty_answer,
        test_mock_client,
        test_evaluator_interface_compatibility,
        test_full_evaluation_flow
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n✅ All LLM evaluator tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

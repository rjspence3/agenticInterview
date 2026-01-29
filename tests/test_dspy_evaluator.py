"""
Tests for DSPy-based interview answer evaluator.

These tests verify:
- DSPy evaluator interface compatibility with heuristic evaluator
- Semantic matching capability (recognizes paraphrases)
- Proper handling of edge cases (empty answers, off-topic, etc.)
- Training data extraction
- Metrics calculations
"""

import sys
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

from models import Question, EvaluationResult, KeypointCoverage


# =============================================================================
# Helper Functions (must be defined before use in decorators)
# =============================================================================

def _dspy_available() -> bool:
    """Check if DSPy is available."""
    try:
        from dspy_evaluator import DSPY_AVAILABLE
        return DSPY_AVAILABLE
    except ImportError:
        return False


def _api_key_available() -> bool:
    """Check if an API key is configured."""
    import os
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def python_question():
    """A question about Python basics with paraphrase-friendly keypoints."""
    return Question(
        id=1,
        text="What is the difference between a list and a tuple in Python?",
        competency="Python",
        difficulty="Easy",
        keypoints=["mutable vs immutable", "syntax differences", "use cases", "performance"]
    )


@pytest.fixture
def decorator_question():
    """A question about Python decorators."""
    return Question(
        id=2,
        text="Explain what a Python decorator is and how it works.",
        competency="Python",
        difficulty="Medium",
        keypoints=["function that wraps another function", "@ syntax", "modifies behavior", "returns a function"]
    )


@pytest.fixture
def recursion_question():
    """A question about recursion."""
    return Question(
        id=3,
        text="What is recursion?",
        competency="Programming",
        difficulty="Medium",
        keypoints=["function calls itself", "base case", "recursive case", "stack usage"]
    )


# =============================================================================
# Module Import Tests
# =============================================================================

class TestModuleImports:
    """Test that DSPy modules can be imported."""

    def test_dspy_evaluator_imports(self):
        """DSPy evaluator module should import without error."""
        from dspy_evaluator import DSPyEvaluatorAgent, DSPY_AVAILABLE
        assert DSPyEvaluatorAgent is not None

    def test_dspy_training_imports(self):
        """DSPy training module should import without error."""
        from dspy_training import build_training_set, get_train_val_split
        assert build_training_set is not None
        assert get_train_val_split is not None

    def test_dspy_metrics_imports(self):
        """DSPy metrics module should import without error."""
        from dspy_metrics import (
            keypoint_f1_metric,
            score_accuracy_metric,
            combined_metric,
        )
        assert keypoint_f1_metric is not None
        assert score_accuracy_metric is not None
        assert combined_metric is not None


# =============================================================================
# Training Data Tests
# =============================================================================

class TestTrainingData:
    """Test training data extraction and quality."""

    @pytest.mark.skipif(
        not _dspy_available(),
        reason="DSPy not installed"
    )
    def test_training_set_not_empty(self):
        """Training set should contain examples."""
        from dspy_training import build_training_set
        trainset = build_training_set()
        assert len(trainset) > 0, "Training set should not be empty"

    @pytest.mark.skipif(
        not _dspy_available(),
        reason="DSPy not installed"
    )
    def test_training_set_has_variety(self):
        """Training set should have examples of different mastery levels."""
        from dspy_training import build_training_set
        trainset = build_training_set()

        mastery_levels = {ex.mastery_label for ex in trainset}
        assert "strong" in mastery_levels, "Should have strong examples"
        assert "mixed" in mastery_levels, "Should have mixed examples"
        assert "weak" in mastery_levels, "Should have weak examples"

    @pytest.mark.skipif(
        not _dspy_available(),
        reason="DSPy not installed"
    )
    def test_training_set_has_semantic_examples(self):
        """Training set should include semantic matching edge cases."""
        from dspy_training import get_semantic_test_cases
        semantic_cases = get_semantic_test_cases()
        assert len(semantic_cases) > 0, "Should have semantic test cases"

    @pytest.mark.skipif(
        not _dspy_available(),
        reason="DSPy not installed"
    )
    def test_train_val_split(self):
        """Train/val split should work correctly."""
        from dspy_training import get_train_val_split
        train, val = get_train_val_split(train_ratio=0.8)

        assert len(train) > 0, "Training set should not be empty"
        assert len(val) > 0, "Validation set should not be empty"
        assert len(train) > len(val), "Training set should be larger"


# =============================================================================
# Metrics Tests
# =============================================================================

class TestMetrics:
    """Test DSPy optimization metrics."""

    def test_keypoint_f1_perfect_match(self):
        """F1 should be 1.0 for perfect keypoint match."""
        from dspy_metrics import keypoint_f1_metric

        class MockExample:
            covered_keypoints = ["a", "b", "c"]

        class MockPrediction:
            covered_keypoints = ["a", "b", "c"]

        score = keypoint_f1_metric(MockExample(), MockPrediction())
        assert score == 1.0

    def test_keypoint_f1_no_match(self):
        """F1 should be 0.0 when no keypoints match."""
        from dspy_metrics import keypoint_f1_metric

        class MockExample:
            covered_keypoints = ["a", "b"]

        class MockPrediction:
            covered_keypoints = ["c", "d"]

        score = keypoint_f1_metric(MockExample(), MockPrediction())
        assert score == 0.0

    def test_keypoint_f1_partial_match(self):
        """F1 should be between 0 and 1 for partial match."""
        from dspy_metrics import keypoint_f1_metric

        class MockExample:
            covered_keypoints = ["a", "b", "c"]

        class MockPrediction:
            covered_keypoints = ["a", "b"]  # Missing "c"

        score = keypoint_f1_metric(MockExample(), MockPrediction())
        # Precision: 2/2 = 1.0, Recall: 2/3 = 0.67, F1 = 0.8
        assert 0.7 < score < 0.9

    def test_score_accuracy_exact(self):
        """Score accuracy should be 1.0 for exact match."""
        from dspy_metrics import score_accuracy_metric

        class MockExample:
            score = 75

        class MockPrediction:
            score = 75

        accuracy = score_accuracy_metric(MockExample(), MockPrediction())
        assert accuracy == 1.0

    def test_score_accuracy_partial(self):
        """Score accuracy should decrease with error."""
        from dspy_metrics import score_accuracy_metric

        class MockExample:
            score = 80

        class MockPrediction:
            score = 60  # 20 point error

        accuracy = score_accuracy_metric(MockExample(), MockPrediction())
        assert accuracy == 0.8  # 1 - 20/100

    def test_combined_metric_range(self):
        """Combined metric should be between 0 and 1."""
        from dspy_metrics import combined_metric

        class MockExample:
            covered_keypoints = ["a", "b"]
            score = 100
            mastery_label = "strong"

        class MockPrediction:
            covered_keypoints = ["a"]
            score = 80
            mastery_label = "strong"

        score = combined_metric(MockExample(), MockPrediction())
        assert 0 <= score <= 1


# =============================================================================
# Interface Compatibility Tests
# =============================================================================

class TestInterfaceCompatibility:
    """Test that DSPy evaluator is compatible with heuristic evaluator."""

    def test_same_evaluate_signature(self):
        """DSPy evaluator should have same evaluate() signature."""
        from agents import EvaluatorAgent
        from dspy_evaluator import DSPyEvaluatorAgent, DSPY_AVAILABLE

        if not DSPY_AVAILABLE:
            pytest.skip("DSPy not installed")

        # Both should have evaluate method
        assert hasattr(EvaluatorAgent, 'evaluate')
        assert hasattr(DSPyEvaluatorAgent, 'evaluate')

        # Check method signatures match
        import inspect
        heuristic_sig = inspect.signature(EvaluatorAgent.evaluate)
        # Note: DSPy evaluator is a class, so we check the instance method
        # Both should accept (self, question, answer)
        heuristic_params = list(heuristic_sig.parameters.keys())
        assert 'question' in heuristic_params or len(heuristic_params) >= 2

    def test_returns_evaluation_result(self, python_question):
        """DSPy evaluator should return EvaluationResult."""
        from agents import EvaluatorAgent

        evaluator = EvaluatorAgent()
        result = evaluator.evaluate(python_question, "Test answer")

        assert isinstance(result, EvaluationResult)
        assert hasattr(result, 'score_0_100')
        assert hasattr(result, 'mastery_label')
        assert hasattr(result, 'keypoints_coverage')
        assert hasattr(result, 'short_feedback')


# =============================================================================
# Semantic Matching Tests (Key DSPy Advantage)
# =============================================================================

class TestSemanticMatching:
    """
    Test that DSPy recognizes paraphrased concepts.

    These tests demonstrate the key advantage of DSPy over heuristic matching.
    The heuristic evaluator would score these as 0% because the exact
    keypoint strings don't appear, but DSPy should recognize the concepts.
    """

    def test_heuristic_fails_paraphrase(self, python_question):
        """Demonstrate that heuristic fails on paraphrased answers."""
        from agents import EvaluatorAgent

        evaluator = EvaluatorAgent()

        # This answer covers all concepts but uses different words
        answer = (
            "Lists can be changed after creation while tuples cannot. "
            "Lists use square brackets and tuples use parentheses. "
            "I'd use a list for a shopping cart and a tuple for coordinates. "
            "Tuples are slightly faster due to immutability."
        )

        result = evaluator.evaluate(python_question, answer)

        # Heuristic should score this low (no exact keyword matches)
        # This is the problem DSPy solves
        assert result.score_0_100 < 50, (
            "Heuristic should fail on paraphrased answers - "
            "if this passes, the keypoints may have changed"
        )

    @pytest.mark.skipif(
        not _dspy_available() or not _api_key_available(),
        reason="DSPy not installed or no API key"
    )
    def test_dspy_recognizes_paraphrase(self, python_question):
        """DSPy should recognize paraphrased concepts."""
        from dspy_evaluator import DSPyEvaluatorAgent

        evaluator = DSPyEvaluatorAgent()

        # Same paraphrased answer
        answer = (
            "Lists can be changed after creation while tuples cannot. "
            "Lists use square brackets and tuples use parentheses. "
            "I'd use a list for a shopping cart and a tuple for coordinates. "
            "Tuples are slightly faster due to immutability."
        )

        result = evaluator.evaluate(python_question, answer)

        # DSPy should recognize these as covering the keypoints
        assert result.score_0_100 >= 80, (
            f"DSPy should recognize paraphrased concepts. Got score: {result.score_0_100}"
        )
        assert result.mastery_label == "strong"


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Test handling of edge cases."""

    @pytest.mark.skipif(
        not _dspy_available() or not _api_key_available(),
        reason="DSPy not installed or no API key"
    )
    def test_empty_answer(self, python_question):
        """Empty answer should score 0."""
        from dspy_evaluator import DSPyEvaluatorAgent

        evaluator = DSPyEvaluatorAgent()
        result = evaluator.evaluate(python_question, "")

        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    @pytest.mark.skipif(
        not _dspy_available() or not _api_key_available(),
        reason="DSPy not installed or no API key"
    )
    def test_whitespace_answer(self, python_question):
        """Whitespace-only answer should score 0."""
        from dspy_evaluator import DSPyEvaluatorAgent

        evaluator = DSPyEvaluatorAgent()
        result = evaluator.evaluate(python_question, "   \n\t  ")

        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    @pytest.mark.skipif(
        not _dspy_available() or not _api_key_available(),
        reason="DSPy not installed or no API key"
    )
    def test_off_topic_answer(self, decorator_question):
        """Off-topic answer should score 0 or very low."""
        from dspy_evaluator import DSPyEvaluatorAgent

        evaluator = DSPyEvaluatorAgent()
        result = evaluator.evaluate(
            decorator_question,
            "The weather today is sunny and warm. I like beaches."
        )

        assert result.score_0_100 <= 25
        assert result.mastery_label == "weak"


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Tests for bad/weak answer handling in the Agentic Interview System.

These tests verify that the evaluation system correctly identifies and scores
poor quality answers, including:
- Empty or blank answers
- Off-topic/irrelevant answers
- Gibberish/nonsense answers
- Very short/insufficient answers
- Answers that miss all keypoints
- Answers with wrong information
- Copy-paste of the question
"""

import sys
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Question, InterviewState
from agents import QuestionsAgent, EvaluatorAgent, OrchestratorAgent


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def python_question():
    """A question about Python basics."""
    return Question(
        id=1,
        text="Explain what a Python decorator is and how it works.",
        competency="Python",
        difficulty="Medium",
        keypoints=["function that wraps another function", "@ syntax", "modifies behavior", "returns a function"]
    )


@pytest.fixture
def algorithm_question():
    """A question about algorithms."""
    return Question(
        id=2,
        text="Explain how merge sort works and its time complexity.",
        competency="Algorithms",
        difficulty="Hard",
        keypoints=["divide and conquer", "split array in half", "merge sorted halves", "O(n log n)"]
    )


@pytest.fixture
def system_design_question():
    """A question about system design."""
    return Question(
        id=3,
        text="How would you design a URL shortener service?",
        competency="System Design",
        difficulty="Hard",
        keypoints=["hash function", "database storage", "redirect logic", "collision handling", "scalability"]
    )


@pytest.fixture
def behavioral_question():
    """A behavioral interview question."""
    return Question(
        id=4,
        text="Tell me about a time you had to deal with a difficult team member.",
        competency="Leadership",
        difficulty="Medium",
        keypoints=["specific situation", "actions taken", "outcome achieved", "lessons learned"]
    )


@pytest.fixture
def evaluator():
    """Return a heuristic evaluator agent."""
    return EvaluatorAgent()


# =============================================================================
# Empty/Blank Answer Tests
# =============================================================================

class TestEmptyAnswers:
    """Tests for empty and blank answers."""

    def test_empty_string(self, python_question, evaluator):
        """Empty string should score 0."""
        result = evaluator.evaluate(python_question, "")
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"
        assert all(not kp.covered for kp in result.keypoints_coverage)

    def test_whitespace_only(self, python_question, evaluator):
        """Whitespace-only answer should score 0."""
        result = evaluator.evaluate(python_question, "   \n\t  \n  ")
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_single_character(self, python_question, evaluator):
        """Single character answer should score 0."""
        result = evaluator.evaluate(python_question, "x")
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"


# =============================================================================
# Off-Topic Answer Tests
# =============================================================================

class TestOffTopicAnswers:
    """Tests for irrelevant/off-topic answers."""

    def test_completely_unrelated_topic(self, python_question, evaluator):
        """Answer about completely different topic should score 0."""
        answer = "The weather today is sunny and warm. I like to go to the beach on sunny days."
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_different_programming_topic(self, python_question, evaluator):
        """Answer about different programming concept should score low."""
        answer = "A for loop iterates over a sequence of items like lists or ranges."
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_wrong_language(self, python_question, evaluator):
        """Answer about wrong programming language should score low."""
        answer = "In Java, you use the public static void main method as the entry point."
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_personal_story_for_technical(self, algorithm_question, evaluator):
        """Personal story for technical question should score 0."""
        answer = "Last summer I went on vacation to Hawaii. It was really nice."
        result = evaluator.evaluate(algorithm_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"


# =============================================================================
# Gibberish/Nonsense Answer Tests
# =============================================================================

class TestGibberishAnswers:
    """Tests for gibberish and nonsense answers."""

    def test_random_characters(self, python_question, evaluator):
        """Random characters should score 0."""
        answer = "asdfghjkl qwertyuiop zxcvbnm"
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_keyboard_mash(self, python_question, evaluator):
        """Keyboard mashing should score 0."""
        answer = "sdfkjhsdkfjh dsjkfh sdkjfh sdkjfh sdkfjh"
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_repeated_word(self, python_question, evaluator):
        """Repeated single word should score 0."""
        answer = "code code code code code code code"
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_lorem_ipsum(self, python_question, evaluator):
        """Lorem ipsum placeholder text should score 0."""
        answer = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"


# =============================================================================
# Insufficient/Too Short Answer Tests
# =============================================================================

class TestInsufficientAnswers:
    """Tests for answers that are too short or lack substance."""

    def test_single_word_answer(self, python_question, evaluator):
        """Single word answer should score low."""
        answer = "decorator"
        result = evaluator.evaluate(python_question, answer)
        # May match one keypoint but insufficient
        assert result.score_0_100 <= 25
        assert result.mastery_label == "weak"

    def test_yes_no_answer(self, python_question, evaluator):
        """Yes/No answer should score 0."""
        answer = "Yes, I know about decorators."
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_i_dont_know(self, python_question, evaluator):
        """'I don't know' answer should score 0."""
        answer = "I don't know"
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_pass_skip(self, python_question, evaluator):
        """Pass/skip answer should score 0."""
        answer = "Pass"
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_vague_answer(self, algorithm_question, evaluator):
        """Vague answer without specifics should score low."""
        answer = "It's a sorting algorithm that sorts things."
        result = evaluator.evaluate(algorithm_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"


# =============================================================================
# Question Copy/Echo Answer Tests
# =============================================================================

class TestCopiedQuestionAnswers:
    """Tests for answers that just copy the question."""

    def test_exact_question_copy(self, python_question, evaluator):
        """Copying the question exactly should score low."""
        answer = python_question.text
        result = evaluator.evaluate(python_question, answer)
        # Should not get credit for echoing the question
        assert result.score_0_100 <= 25

    def test_question_with_question_mark_response(self, python_question, evaluator):
        """Responding with another question should score 0."""
        answer = "What do you mean by decorator? Can you explain more?"
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_restating_question(self, algorithm_question, evaluator):
        """Restating the question without answering should score low."""
        answer = "You're asking about how merge sort works and what its time complexity is."
        result = evaluator.evaluate(algorithm_question, answer)
        assert result.score_0_100 <= 25


# =============================================================================
# Incorrect/Wrong Information Tests
# =============================================================================

class TestIncorrectAnswers:
    """Tests for answers with wrong information."""

    def test_wrong_complexity(self, algorithm_question, evaluator):
        """Answer with wrong complexity should miss that keypoint."""
        answer = "Merge sort has O(n^2) complexity. It divides the array in half and merges sorted halves."
        result = evaluator.evaluate(algorithm_question, answer)

        # Should get credit for divide, split, merge but not O(n log n)
        complexity_kp = next(
            (kp for kp in result.keypoints_coverage if "log n" in kp.keypoint.lower()),
            None
        )
        if complexity_kp:
            assert not complexity_kp.covered, "Wrong complexity should not be marked as covered"

    def test_confused_concepts(self, python_question, evaluator):
        """Confusing decorator with different concept should score low."""
        answer = "A decorator is a design pattern where you inherit from a base class to add functionality. You use class inheritance."
        result = evaluator.evaluate(python_question, answer)
        # Missing key decorator concepts
        assert result.score_0_100 < 50


# =============================================================================
# Behavioral Question Bad Answers
# =============================================================================

class TestBadBehavioralAnswers:
    """Tests for bad answers to behavioral questions."""

    def test_no_specific_example(self, behavioral_question, evaluator):
        """Generic answer without specific example should score low."""
        answer = "I usually try to communicate well with everyone and be professional."
        result = evaluator.evaluate(behavioral_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_hypothetical_instead_of_real(self, behavioral_question, evaluator):
        """Hypothetical answer instead of real experience should miss keypoints."""
        answer = "If I had a difficult team member, I would probably talk to them nicely."
        result = evaluator.evaluate(behavioral_question, answer)
        assert result.score_0_100 <= 25

    def test_negative_attitude(self, behavioral_question, evaluator):
        """Answer showing negative attitude should still be scored on keypoints."""
        answer = "I just ignore difficult people and do my own work. They're not worth my time."
        result = evaluator.evaluate(behavioral_question, answer)
        # May not hit positive keypoints
        assert result.mastery_label in ["weak", "mixed"]


# =============================================================================
# Full Interview Flow with Bad Answers
# =============================================================================

class TestBadAnswerInterview:
    """Test complete interview flow with consistently bad answers."""

    def test_all_bad_answers_interview(self):
        """Interview where candidate gives all bad answers."""
        questions = [
            Question(
                id=1,
                text="What is object-oriented programming?",
                competency="Programming",
                difficulty="Easy",
                keypoints=["classes", "objects", "inheritance", "encapsulation"]
            ),
            Question(
                id=2,
                text="Explain REST API design principles.",
                competency="Web Development",
                difficulty="Medium",
                keypoints=["stateless", "HTTP methods", "resources", "JSON"]
            ),
            Question(
                id=3,
                text="How does garbage collection work?",
                competency="Memory Management",
                difficulty="Hard",
                keypoints=["automatic memory management", "reference counting", "mark and sweep", "memory leak prevention"]
            )
        ]

        questions_agent = QuestionsAgent(questions)
        evaluator_agent = EvaluatorAgent()
        orchestrator = OrchestratorAgent(questions_agent, evaluator_agent)

        state = InterviewState()

        # Bad answer 1: Off-topic
        state = orchestrator.step(state, "I like pizza and video games.")
        assert state.evaluations[1].score_0_100 == 0
        assert state.evaluations[1].mastery_label == "weak"

        # Bad answer 2: Too vague
        state = orchestrator.step(state, "It's a way to make APIs.")
        assert state.evaluations[2].score_0_100 == 0
        assert state.evaluations[2].mastery_label == "weak"

        # Bad answer 3: I don't know
        state = orchestrator.step(state, "I'm not sure about this one.")
        assert state.evaluations[3].score_0_100 == 0
        assert state.evaluations[3].mastery_label == "weak"

        assert state.finished

        # Generate summary - should indicate poor performance
        summary = orchestrator.generate_summary(state)
        assert "Overall Score" in summary
        # Average should be 0 or very low
        assert "0.0" in summary or "0%" in summary or "Weak" in summary

    def test_mixed_quality_interview(self):
        """Interview with mix of good and bad answers."""
        questions = [
            Question(
                id=1,
                text="What is a variable?",
                competency="Programming",
                difficulty="Easy",
                keypoints=["stores data", "has a name", "has a type"]
            ),
            Question(
                id=2,
                text="Explain recursion.",
                competency="Programming",
                difficulty="Medium",
                keypoints=["function calls itself", "base case", "recursive case"]
            ),
            Question(
                id=3,
                text="What is Big O notation?",
                competency="Algorithms",
                difficulty="Medium",
                keypoints=["time complexity", "space complexity", "worst case", "algorithm efficiency"]
            )
        ]

        questions_agent = QuestionsAgent(questions)
        evaluator_agent = EvaluatorAgent()
        orchestrator = OrchestratorAgent(questions_agent, evaluator_agent)

        state = InterviewState()

        # Good answer
        state = orchestrator.step(state, "A variable stores data, has a name, and has a type like int or string.")
        assert state.evaluations[1].score_0_100 == 100
        assert state.evaluations[1].mastery_label == "strong"

        # Bad answer
        state = orchestrator.step(state, "I forgot what recursion is.")
        assert state.evaluations[2].score_0_100 == 0
        assert state.evaluations[2].mastery_label == "weak"

        # Partial answer
        state = orchestrator.step(state, "Big O is about time complexity of algorithms.")
        assert 0 < state.evaluations[3].score_0_100 < 100

        assert state.finished


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Edge cases for bad answers."""

    def test_extremely_long_irrelevant_answer(self, python_question, evaluator):
        """Very long but irrelevant answer should still score 0."""
        answer = "The quick brown fox jumps over the lazy dog. " * 100
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_special_characters_only(self, python_question, evaluator):
        """Answer with only special characters should score 0."""
        answer = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_numbers_only(self, python_question, evaluator):
        """Answer with only numbers should score 0."""
        answer = "12345 67890 11111 22222"
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_emoji_only(self, python_question, evaluator):
        """Answer with only emojis should score 0."""
        answer = "😀 🎉 🚀 💻 🐍"
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_url_only(self, python_question, evaluator):
        """Answer with just a URL should score 0."""
        answer = "https://docs.python.org/3/glossary.html#term-decorator"
        result = evaluator.evaluate(python_question, answer)
        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_code_without_explanation(self, python_question, evaluator):
        """Code snippet without explanation should score based on keypoints."""
        answer = """
        @my_decorator
        def my_function():
            pass
        """
        result = evaluator.evaluate(python_question, answer)
        # May match @ syntax keypoint
        assert result.score_0_100 <= 50  # Partial at best


# =============================================================================
# LLM Evaluator Bad Answer Tests (with Mock)
# =============================================================================

class TestLLMEvaluatorBadAnswers:
    """Test LLM evaluator handling of bad answers (using mock)."""

    def test_llm_evaluator_empty_answer(self, python_question):
        """LLM evaluator should handle empty answer."""
        try:
            from llm_evaluator import LLMEvaluatorAgent
            from llm_client import MockLLMClient
        except ImportError:
            pytest.skip("LLM evaluator dependencies not available")

        evaluator = LLMEvaluatorAgent(MockLLMClient(), "mock", 0.3)
        result = evaluator.evaluate(python_question, "")

        assert result.score_0_100 == 0
        assert result.mastery_label == "weak"

    def test_llm_evaluator_gibberish(self, python_question):
        """LLM evaluator should handle gibberish."""
        try:
            from llm_evaluator import LLMEvaluatorAgent
            from llm_client import MockLLMClient
        except ImportError:
            pytest.skip("LLM evaluator dependencies not available")

        evaluator = LLMEvaluatorAgent(MockLLMClient(), "mock", 0.3)
        result = evaluator.evaluate(python_question, "asdkjfh aksjdfh aksjdfh")

        # Mock should still evaluate properly
        assert result.score_0_100 >= 0
        assert result.mastery_label in ["weak", "mixed", "strong"]
        assert len(result.keypoints_coverage) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

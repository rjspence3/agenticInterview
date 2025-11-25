"""
Basic flow tests for the Agentic Interview System.

Tests the core agent functionality without UI dependencies.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Question, InterviewState
from agents import QuestionsAgent, EvaluatorAgent, OrchestratorAgent


def test_questions_agent():
    """Test QuestionsAgent functionality."""
    questions = [
        Question(
            id=1,
            text="What is a list comprehension in Python?",
            competency="Python",
            difficulty="Easy",
            keypoints=["list comprehension", "syntax", "iterable"]
        ),
        Question(
            id=2,
            text="Explain time complexity of binary search.",
            competency="Algorithms",
            difficulty="Medium",
            keypoints=["O(log n)", "divide and conquer", "sorted array"]
        )
    ]

    agent = QuestionsAgent(questions)

    # Test count
    assert agent.count() == 2, "Should have 2 questions"

    # Test get_next_question
    q1 = agent.get_next_question(0)
    assert q1 is not None, "Should get first question"
    assert q1.id == 1, "First question should have id 1"

    q2 = agent.get_next_question(1)
    assert q2 is not None, "Should get second question"
    assert q2.id == 2, "Second question should have id 2"

    # Test out of bounds
    q_none = agent.get_next_question(2)
    assert q_none is None, "Should return None for out of bounds index"

    print("✓ QuestionsAgent tests passed")


def test_evaluator_agent_perfect_answer():
    """Test EvaluatorAgent with perfect answer covering all keypoints."""
    question = Question(
        id=1,
        text="What is a list comprehension?",
        competency="Python",
        difficulty="Easy",
        keypoints=["list comprehension", "syntax", "concise"]
    )

    agent = EvaluatorAgent()

    # Answer that covers all keypoints
    answer = (
        "A list comprehension is a concise Python syntax for creating lists. "
        "It provides a compact way to process iterables."
    )

    result = agent.evaluate(question, answer)

    assert result.question_id == 1, "Should match question id"
    assert result.score_0_100 == 100, f"Should score 100, got {result.score_0_100}"
    assert result.mastery_label == "strong", "Should be labeled as strong"
    assert len(result.keypoints_coverage) == 3, "Should have coverage for all 3 keypoints"

    # Check all keypoints are covered
    covered = [kp.covered for kp in result.keypoints_coverage]
    assert all(covered), "All keypoints should be covered"

    print("✓ EvaluatorAgent perfect answer test passed")


def test_evaluator_agent_partial_answer():
    """Test EvaluatorAgent with partial answer covering some keypoints."""
    question = Question(
        id=2,
        text="Explain binary search complexity.",
        competency="Algorithms",
        difficulty="Medium",
        keypoints=["O(log n)", "divide and conquer", "sorted array"]
    )

    agent = EvaluatorAgent()

    # Answer that covers only 2 out of 3 keypoints
    answer = "Binary search has O(log n) time complexity because it uses divide and conquer."

    result = agent.evaluate(question, answer)

    assert result.question_id == 2, "Should match question id"
    assert 60 <= result.score_0_100 <= 70, f"Should score around 66, got {result.score_0_100}"
    assert result.mastery_label in ["mixed", "strong"], "Should be mixed or strong"

    # Check coverage
    covered_count = sum(1 for kp in result.keypoints_coverage if kp.covered)
    assert covered_count == 2, f"Should cover 2 keypoints, got {covered_count}"

    # Check that "sorted array" is not covered
    sorted_array_coverage = next(
        kp for kp in result.keypoints_coverage if kp.keypoint == "sorted array"
    )
    assert not sorted_array_coverage.covered, "sorted array should not be covered"

    print("✓ EvaluatorAgent partial answer test passed")


def test_evaluator_agent_weak_answer():
    """Test EvaluatorAgent with weak answer covering few keypoints."""
    question = Question(
        id=3,
        text="What is recursion?",
        competency="Programming",
        difficulty="Easy",
        keypoints=["function calls itself", "base case", "recursive case"]
    )

    agent = EvaluatorAgent()

    # Answer that covers none of the keypoints
    answer = "It's a programming technique that is useful sometimes."

    result = agent.evaluate(question, answer)

    assert result.score_0_100 == 0, f"Should score 0, got {result.score_0_100}"
    assert result.mastery_label == "weak", "Should be labeled as weak"

    # Check no keypoints are covered
    covered_count = sum(1 for kp in result.keypoints_coverage if kp.covered)
    assert covered_count == 0, "No keypoints should be covered"

    print("✓ EvaluatorAgent weak answer test passed")


def test_orchestrator_agent_full_flow():
    """Test OrchestratorAgent coordinating a full interview."""
    # Create questions
    questions = [
        Question(
            id=1,
            text="What is Python?",
            competency="Python",
            difficulty="Easy",
            keypoints=["programming language", "interpreted", "dynamic typing"]
        ),
        Question(
            id=2,
            text="What is a hash table?",
            competency="Data Structures",
            difficulty="Medium",
            keypoints=["key-value pairs", "O(1) lookup", "hash function"]
        )
    ]

    # Create agents
    questions_agent = QuestionsAgent(questions)
    evaluator_agent = EvaluatorAgent()
    orchestrator = OrchestratorAgent(questions_agent, evaluator_agent)

    # Start interview
    state = InterviewState()

    # Verify initial state
    assert state.current_index == 0, "Should start at index 0"
    assert not state.finished, "Should not be finished initially"
    assert len(state.evaluations) == 0, "Should have no evaluations initially"

    # Answer first question (partial answer)
    answer1 = "Python is a programming language that is interpreted."
    state = orchestrator.step(state, answer1)

    assert state.current_index == 1, "Should advance to index 1"
    assert not state.finished, "Should not be finished after 1 of 2 questions"
    assert len(state.evaluations) == 1, "Should have 1 evaluation"
    assert 1 in state.evaluations, "Should have evaluation for question 1"

    # Check first evaluation
    eval1 = state.evaluations[1]
    assert eval1.score_0_100 > 0, "Should have some score for partial answer"
    assert eval1.score_0_100 < 100, "Should not be perfect score"

    # Answer second question (good answer)
    answer2 = "A hash table stores key-value pairs and provides O(1) lookup using a hash function."
    state = orchestrator.step(state, answer2)

    assert state.current_index == 2, "Should advance to index 2"
    assert state.finished, "Should be finished after answering all questions"
    assert len(state.evaluations) == 2, "Should have 2 evaluations"
    assert 2 in state.evaluations, "Should have evaluation for question 2"

    # Check second evaluation
    eval2 = state.evaluations[2]
    assert eval2.score_0_100 == 100, "Should have perfect score for covering all keypoints"

    # Test summary generation
    summary = orchestrator.generate_summary(state)
    assert "Overall Score" in summary, "Summary should include overall score"
    assert "Interview Complete" in summary, "Summary should indicate completion"

    print("✓ OrchestratorAgent full flow test passed")


def test_empty_answer_handling():
    """Test that empty answers are handled gracefully."""
    questions = [
        Question(
            id=1,
            text="Test question",
            competency="Test",
            difficulty="Easy",
            keypoints=["test"]
        )
    ]

    questions_agent = QuestionsAgent(questions)
    evaluator_agent = EvaluatorAgent()
    orchestrator = OrchestratorAgent(questions_agent, evaluator_agent)

    state = InterviewState()

    # Submit empty answer
    state = orchestrator.step(state, "")

    # Should not advance or evaluate
    assert state.current_index == 0, "Should not advance on empty answer"
    assert len(state.evaluations) == 0, "Should not create evaluation for empty answer"

    print("✓ Empty answer handling test passed")


def test_llm_evaluator_integration():
    """Test that LLM evaluator works in full interview flow (with mock)."""
    try:
        from llm_evaluator import LLMEvaluatorAgent
        from llm_client import MockLLMClient
    except ImportError:
        print("⚠ Skipping LLM evaluator test (dependencies not installed)")
        return

    print("\n=== Testing LLM Evaluator Integration ===")

    # Create questions
    questions = [
        Question(
            id=1,
            text="What is recursion?",
            competency="Programming",
            difficulty="Medium",
            keypoints=["base case", "recursive case", "stack usage"]
        ),
        Question(
            id=2,
            text="Explain binary search.",
            competency="Algorithms",
            difficulty="Medium",
            keypoints=["O(log n)", "sorted array", "divide and conquer"]
        )
    ]

    # Create agents with LLM evaluator (using mock)
    questions_agent = QuestionsAgent(questions)
    llm_evaluator = LLMEvaluatorAgent(MockLLMClient(), "mock", 0.3)
    orchestrator = OrchestratorAgent(questions_agent, llm_evaluator)

    # Run interview
    state = InterviewState()

    # Answer first question
    answer1 = "Recursion is when a function calls itself. You need a base case to stop."
    state = orchestrator.step(state, answer1)

    assert len(state.evaluations) == 1, "Should have 1 evaluation"
    eval1 = state.evaluations[1]
    assert eval1.score_0_100 >= 0 and eval1.score_0_100 <= 100, "Score should be 0-100"
    assert eval1.mastery_label in ["strong", "mixed", "weak"], "Should have valid mastery label"
    assert len(eval1.keypoints_coverage) == 3, "Should have coverage for all keypoints"
    assert eval1.short_feedback, "Should have feedback"

    # Answer second question
    answer2 = "Binary search has O(log n) complexity, works on sorted arrays using divide and conquer."
    state = orchestrator.step(state, answer2)

    assert len(state.evaluations) == 2, "Should have 2 evaluations"
    assert state.finished, "Interview should be finished"

    eval2 = state.evaluations[2]
    assert eval2.score_0_100 == 100, "Perfect answer should score 100"
    assert eval2.mastery_label == "strong", "Perfect answer should be strong"

    # Generate summary
    summary = orchestrator.generate_summary(state)
    assert "Overall Score" in summary, "Summary should include overall score"

    print("✓ LLM evaluator integration test passed")


def run_all_tests():
    """Run all tests."""
    print("Running Agentic Interview System Tests...\n")

    test_questions_agent()
    test_evaluator_agent_perfect_answer()
    test_evaluator_agent_partial_answer()
    test_evaluator_agent_weak_answer()
    test_orchestrator_agent_full_flow()
    test_empty_answer_handling()
    test_llm_evaluator_integration()

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    run_all_tests()

"""
DSPy training data extraction for interview evaluator optimization.

Converts existing test fixtures and seed data into DSPy Example objects
that can be used for BootstrapFewShot optimization.
"""

from typing import Optional

try:
    import dspy
except ImportError:
    dspy = None  # Allow module to load without dspy for introspection


def build_training_set() -> list:
    """
    Build a comprehensive training set from test fixtures and seed data.

    Returns:
        List of dspy.Example objects with inputs and expected outputs.
    """
    if dspy is None:
        raise ImportError("dspy-ai is required. Install with: pip install dspy-ai")

    examples = []

    # ==========================================================================
    # PERFECT ANSWERS (Score: 100, Mastery: strong)
    # ==========================================================================

    # Python list comprehension - perfect answer
    examples.append(_create_example(
        question_text="What is a list comprehension in Python?",
        answer="A list comprehension is a concise Python syntax for creating lists. It provides a compact way to process iterables.",
        keypoints=["list comprehension", "syntax", "concise"],
        difficulty="Easy",
        covered_keypoints=["list comprehension", "syntax", "concise"],
        missed_keypoints=[],
        score=100,
        mastery_label="strong",
        feedback="Excellent! Covered all keypoints with clear explanation.",
        follow_up=""
    ))

    # Recursion - comprehensive answer
    examples.append(_create_example(
        question_text="What is recursion?",
        answer="Recursion is when a function calls itself. You need a base case to stop the recursion and a recursive case that moves toward the base case. Each call adds to the stack.",
        keypoints=["function calls itself", "base case", "recursive case", "stack usage"],
        difficulty="Medium",
        covered_keypoints=["function calls itself", "base case", "recursive case", "stack usage"],
        missed_keypoints=[],
        score=100,
        mastery_label="strong",
        feedback="Comprehensive answer covering all aspects of recursion.",
        follow_up=""
    ))

    # Python decorators - full coverage
    examples.append(_create_example(
        question_text="Explain what a Python decorator is and how it works.",
        answer="A decorator is a function that wraps another function to modify its behavior. You use the @ syntax above a function definition. The decorator returns a function that typically calls the original function with added functionality.",
        keypoints=["function that wraps another function", "@ syntax", "modifies behavior", "returns a function"],
        difficulty="Medium",
        covered_keypoints=["function that wraps another function", "@ syntax", "modifies behavior", "returns a function"],
        missed_keypoints=[],
        score=100,
        mastery_label="strong",
        feedback="Excellent explanation covering all key decorator concepts.",
        follow_up=""
    ))

    # List vs Tuple - semantic coverage (key test case!)
    examples.append(_create_example(
        question_text="What is the difference between a list and a tuple in Python?",
        answer="Lists can be changed after creation while tuples cannot. Lists use square brackets and tuples use parentheses. I'd use a list for a shopping cart and a tuple for coordinates. Tuples are slightly faster due to immutability.",
        keypoints=["mutable vs immutable", "syntax differences", "use cases", "performance"],
        difficulty="Easy",
        covered_keypoints=["mutable vs immutable", "syntax differences", "use cases", "performance"],
        missed_keypoints=[],
        score=100,
        mastery_label="strong",
        feedback="Great answer covering mutability, syntax, use cases, and performance.",
        follow_up=""
    ))

    # GIL explanation
    examples.append(_create_example(
        question_text="What is the GIL and how does it affect multithreading in Python?",
        answer="The Global Interpreter Lock is a mutex that protects access to Python objects, ensuring thread safety. It limits true parallel execution in CPU-bound threads, affecting performance. For CPU work, use multiprocessing instead.",
        keypoints=["GIL definition", "thread safety", "performance impact", "alternatives like multiprocessing"],
        difficulty="Hard",
        covered_keypoints=["GIL definition", "thread safety", "performance impact", "alternatives like multiprocessing"],
        missed_keypoints=[],
        score=100,
        mastery_label="strong",
        feedback="Thorough understanding of GIL and its implications.",
        follow_up=""
    ))

    # ==========================================================================
    # PARTIAL ANSWERS (Score: 50-79, Mastery: mixed)
    # ==========================================================================

    # Binary search - missing sorted array requirement
    examples.append(_create_example(
        question_text="Explain time complexity of binary search.",
        answer="Binary search has O(log n) time complexity because it uses divide and conquer to halve the search space each time.",
        keypoints=["O(log n)", "divide and conquer", "sorted array"],
        difficulty="Medium",
        covered_keypoints=["O(log n)", "divide and conquer"],
        missed_keypoints=["sorted array"],
        score=66,
        mastery_label="mixed",
        feedback="Good on complexity, but missed the sorted array prerequisite.",
        follow_up="What prerequisite must the input array have for binary search to work?"
    ))

    # Merge sort - missing time complexity
    examples.append(_create_example(
        question_text="Explain how merge sort works and its time complexity.",
        answer="Merge sort uses divide and conquer. It splits the array in half recursively, then merges the sorted halves back together.",
        keypoints=["divide and conquer", "split array in half", "merge sorted halves", "O(n log n)"],
        difficulty="Hard",
        covered_keypoints=["divide and conquer", "split array in half", "merge sorted halves"],
        missed_keypoints=["O(n log n)"],
        score=75,
        mastery_label="mixed",
        feedback="Good explanation of the algorithm, but didn't mention time complexity.",
        follow_up="What is the time complexity of merge sort?"
    ))

    # URL shortener - partial design
    examples.append(_create_example(
        question_text="How would you design a URL shortener service?",
        answer="I would use a hash function to generate short codes and store the mapping in a database. When users access the short URL, we redirect them to the original.",
        keypoints=["hash function", "database storage", "redirect logic", "collision handling", "scalability"],
        difficulty="Hard",
        covered_keypoints=["hash function", "database storage", "redirect logic"],
        missed_keypoints=["collision handling", "scalability"],
        score=60,
        mastery_label="mixed",
        feedback="Basic design covered but missing collision handling and scalability discussion.",
        follow_up="How would you handle hash collisions?"
    ))

    # Behavioral - missing outcome
    examples.append(_create_example(
        question_text="Tell me about a time you had to deal with a difficult team member.",
        answer="In my last project, there was a developer who was consistently late to meetings. I scheduled a one-on-one to understand their situation and learned they had a conflicting timezone. We adjusted meeting times.",
        keypoints=["specific situation", "actions taken", "outcome achieved", "lessons learned"],
        difficulty="Medium",
        covered_keypoints=["specific situation", "actions taken"],
        missed_keypoints=["outcome achieved", "lessons learned"],
        score=50,
        mastery_label="mixed",
        feedback="Good specific example with actions, but didn't describe the outcome or lessons.",
        follow_up="What was the outcome of adjusting the meeting times?"
    ))

    # Generators - missing yield keyword
    examples.append(_create_example(
        question_text="When would you use a generator instead of a list?",
        answer="Generators are good for large datasets because they use lazy evaluation and are memory efficient. You don't load everything into memory at once.",
        keypoints=["lazy evaluation", "memory efficiency", "yield keyword", "use cases"],
        difficulty="Medium",
        covered_keypoints=["lazy evaluation", "memory efficiency", "use cases"],
        missed_keypoints=["yield keyword"],
        score=75,
        mastery_label="mixed",
        feedback="Good on benefits but didn't mention the yield keyword.",
        follow_up="What keyword do you use to create a generator function?"
    ))

    # ==========================================================================
    # WEAK ANSWERS (Score: 0-49, Mastery: weak)
    # ==========================================================================

    # Empty answer
    examples.append(_create_example(
        question_text="Explain what a Python decorator is and how it works.",
        answer="",
        keypoints=["function that wraps another function", "@ syntax", "modifies behavior", "returns a function"],
        difficulty="Medium",
        covered_keypoints=[],
        missed_keypoints=["function that wraps another function", "@ syntax", "modifies behavior", "returns a function"],
        score=0,
        mastery_label="weak",
        feedback="No answer provided.",
        follow_up="Can you explain what a decorator does?"
    ))

    # Off-topic answer
    examples.append(_create_example(
        question_text="Explain what a Python decorator is and how it works.",
        answer="The weather today is sunny and warm. I like to go to the beach on sunny days.",
        keypoints=["function that wraps another function", "@ syntax", "modifies behavior", "returns a function"],
        difficulty="Medium",
        covered_keypoints=[],
        missed_keypoints=["function that wraps another function", "@ syntax", "modifies behavior", "returns a function"],
        score=0,
        mastery_label="weak",
        feedback="Answer is completely off-topic.",
        follow_up="Let's try again: what is a Python decorator?"
    ))

    # Single word answer
    examples.append(_create_example(
        question_text="Explain what a Python decorator is and how it works.",
        answer="decorator",
        keypoints=["function that wraps another function", "@ syntax", "modifies behavior", "returns a function"],
        difficulty="Medium",
        covered_keypoints=[],
        missed_keypoints=["function that wraps another function", "@ syntax", "modifies behavior", "returns a function"],
        score=0,
        mastery_label="weak",
        feedback="Answer is too brief to demonstrate understanding.",
        follow_up="Can you explain in more detail what a decorator does?"
    ))

    # Wrong information
    examples.append(_create_example(
        question_text="Explain how merge sort works and its time complexity.",
        answer="Merge sort is O(n^2) because it compares every element to every other element.",
        keypoints=["divide and conquer", "split array in half", "merge sorted halves", "O(n log n)"],
        difficulty="Hard",
        covered_keypoints=[],
        missed_keypoints=["divide and conquer", "split array in half", "merge sorted halves", "O(n log n)"],
        score=0,
        mastery_label="weak",
        feedback="Incorrect complexity - merge sort is O(n log n), not O(n^2).",
        follow_up="Merge sort doesn't compare every pair. What approach does it use?"
    ))

    # Vague answer with no specifics
    examples.append(_create_example(
        question_text="What is recursion?",
        answer="It's a programming technique that is useful sometimes.",
        keypoints=["function calls itself", "base case", "recursive case", "stack usage"],
        difficulty="Medium",
        covered_keypoints=[],
        missed_keypoints=["function calls itself", "base case", "recursive case", "stack usage"],
        score=0,
        mastery_label="weak",
        feedback="Too vague - doesn't explain what recursion actually is.",
        follow_up="Can you describe the specific mechanism of how recursion works?"
    ))

    # Different programming language
    examples.append(_create_example(
        question_text="Explain what a Python decorator is and how it works.",
        answer="In Java, you use the public static void main method as the entry point.",
        keypoints=["function that wraps another function", "@ syntax", "modifies behavior", "returns a function"],
        difficulty="Medium",
        covered_keypoints=[],
        missed_keypoints=["function that wraps another function", "@ syntax", "modifies behavior", "returns a function"],
        score=0,
        mastery_label="weak",
        feedback="Answer discusses Java, not Python decorators.",
        follow_up="Let's focus on Python - what does a decorator do?"
    ))

    # Copy of question (evasion)
    examples.append(_create_example(
        question_text="How would you design a URL shortener service?",
        answer="I would design a URL shortener service by designing a URL shortener service.",
        keypoints=["hash function", "database storage", "redirect logic", "collision handling", "scalability"],
        difficulty="Hard",
        covered_keypoints=[],
        missed_keypoints=["hash function", "database storage", "redirect logic", "collision handling", "scalability"],
        score=0,
        mastery_label="weak",
        feedback="Answer just restates the question without providing design details.",
        follow_up="What specific components would your URL shortener have?"
    ))

    # "I don't know" answer
    examples.append(_create_example(
        question_text="What is the GIL and how does it affect multithreading in Python?",
        answer="I don't know what that is.",
        keypoints=["GIL definition", "thread safety", "performance impact", "alternatives like multiprocessing"],
        difficulty="Hard",
        covered_keypoints=[],
        missed_keypoints=["GIL definition", "thread safety", "performance impact", "alternatives like multiprocessing"],
        score=0,
        mastery_label="weak",
        feedback="Candidate does not know this topic.",
        follow_up="GIL stands for Global Interpreter Lock. Have you worked with threading in Python?"
    ))

    # Generic behavioral (no specific example)
    examples.append(_create_example(
        question_text="Tell me about a time you had to deal with a difficult team member.",
        answer="I usually try to communicate well with my team members and resolve conflicts professionally.",
        keypoints=["specific situation", "actions taken", "outcome achieved", "lessons learned"],
        difficulty="Medium",
        covered_keypoints=[],
        missed_keypoints=["specific situation", "actions taken", "outcome achieved", "lessons learned"],
        score=0,
        mastery_label="weak",
        feedback="Answer is generic without a specific example.",
        follow_up="Can you share a specific situation where you dealt with a difficult team member?"
    ))

    # ==========================================================================
    # SEMANTIC MATCHING EDGE CASES (Critical for DSPy training)
    # ==========================================================================

    # Paraphrased "mutable vs immutable" as "can be changed"
    examples.append(_create_example(
        question_text="What is the difference between a list and a tuple in Python?",
        answer="The main difference is that lists can be modified after you create them but tuples are fixed and cannot be altered. Lists are defined with square brackets [], tuples with parentheses ().",
        keypoints=["mutable vs immutable", "syntax differences"],
        difficulty="Easy",
        covered_keypoints=["mutable vs immutable", "syntax differences"],
        missed_keypoints=[],
        score=100,
        mastery_label="strong",
        feedback="Correctly explains mutability and syntax differences.",
        follow_up=""
    ))

    # Paraphrased "divide and conquer" as "splits in half repeatedly"
    examples.append(_create_example(
        question_text="Explain how binary search works.",
        answer="Binary search repeatedly splits the sorted array in half, comparing the target to the middle element. If the target is smaller, search the left half; if larger, search the right. This gives O(log n) performance.",
        keypoints=["O(log n)", "divide and conquer", "sorted array", "comparison"],
        difficulty="Medium",
        covered_keypoints=["O(log n)", "divide and conquer", "sorted array", "comparison"],
        missed_keypoints=[],
        score=100,
        mastery_label="strong",
        feedback="Excellent explanation of binary search algorithm.",
        follow_up=""
    ))

    # Paraphrased "function calls itself" as "invokes itself"
    examples.append(_create_example(
        question_text="What is recursion?",
        answer="Recursion is a technique where a function invokes itself to solve a problem. It needs a stopping condition (base case) and should make progress toward that condition in each call (recursive case).",
        keypoints=["function calls itself", "base case", "recursive case"],
        difficulty="Easy",
        covered_keypoints=["function calls itself", "base case", "recursive case"],
        missed_keypoints=[],
        score=100,
        mastery_label="strong",
        feedback="Clear explanation of recursion with proper terminology.",
        follow_up=""
    ))

    # Rate limiter design
    examples.append(_create_example(
        question_text="How would you design a rate limiter for an API?",
        answer="I would use a token bucket algorithm stored in Redis. Each user gets a bucket that refills over time. When they make a request, we decrement the bucket. If empty, we reject with 429. For distributed systems, Redis provides atomic operations.",
        keypoints=["rate limiting algorithms", "token bucket", "distributed systems", "Redis"],
        difficulty="Medium",
        covered_keypoints=["rate limiting algorithms", "token bucket", "distributed systems", "Redis"],
        missed_keypoints=[],
        score=100,
        mastery_label="strong",
        feedback="Comprehensive rate limiter design with good technology choices.",
        follow_up=""
    ))

    # CAP theorem
    examples.append(_create_example(
        question_text="Explain the CAP theorem and when you'd choose AP over CP.",
        answer="CAP theorem states you can only have two of: Consistency, Availability, Partition tolerance. In distributed systems you must handle partitions, so you choose between C and A. I'd choose AP for a social media feed where showing slightly stale posts is better than showing nothing.",
        keypoints=["CAP theorem definition", "consistency", "availability", "partition tolerance", "trade-offs"],
        difficulty="Hard",
        covered_keypoints=["CAP theorem definition", "consistency", "availability", "partition tolerance", "trade-offs"],
        missed_keypoints=[],
        score=100,
        mastery_label="strong",
        feedback="Strong understanding of CAP theorem with practical example.",
        follow_up=""
    ))

    return examples


def _create_example(
    question_text: str,
    answer: str,
    keypoints: list[str],
    difficulty: str,
    covered_keypoints: list[str],
    missed_keypoints: list[str],
    score: int,
    mastery_label: str,
    feedback: str,
    follow_up: str,
) -> "dspy.Example":
    """
    Helper to create a DSPy Example with proper input/output specification.

    Args:
        question_text: The interview question
        answer: Candidate's answer
        keypoints: Expected concepts to cover
        difficulty: Easy/Medium/Hard
        covered_keypoints: Which keypoints the answer addresses
        missed_keypoints: Which keypoints were missed
        score: 0-100 score
        mastery_label: strong/mixed/weak
        feedback: Evaluation feedback
        follow_up: Suggested follow-up question

    Returns:
        dspy.Example configured with inputs and outputs
    """
    if dspy is None:
        raise ImportError("dspy-ai is required")

    return dspy.Example(
        question_text=question_text,
        answer=answer,
        keypoints=keypoints,
        difficulty=difficulty,
        covered_keypoints=covered_keypoints,
        missed_keypoints=missed_keypoints,
        score=score,
        mastery_label=mastery_label,
        feedback=feedback,
        follow_up=follow_up
    ).with_inputs("question_text", "answer", "keypoints", "difficulty")


def get_train_val_split(
    train_ratio: float = 0.8
) -> tuple[list, list]:
    """
    Split training data into train and validation sets.

    Args:
        train_ratio: Fraction of data for training (default 0.8)

    Returns:
        Tuple of (train_examples, val_examples)
    """
    examples = build_training_set()
    split_idx = int(len(examples) * train_ratio)
    return examples[:split_idx], examples[split_idx:]


def get_semantic_test_cases() -> list:
    """
    Get examples specifically designed to test semantic matching.

    These are the critical cases where heuristic substring matching fails
    but DSPy should succeed.

    Returns:
        List of dspy.Example objects for semantic matching validation
    """
    if dspy is None:
        raise ImportError("dspy-ai is required")

    return [
        # "can be changed" should match "mutable vs immutable"
        _create_example(
            question_text="Difference between list and tuple?",
            answer="Lists can be changed, tuples cannot.",
            keypoints=["mutable vs immutable"],
            difficulty="Easy",
            covered_keypoints=["mutable vs immutable"],
            missed_keypoints=[],
            score=100,
            mastery_label="strong",
            feedback="Correctly identifies mutability difference.",
            follow_up=""
        ),
        # "splits in half" should match "divide and conquer"
        _create_example(
            question_text="How does binary search work?",
            answer="It repeatedly splits the array in half to find the target.",
            keypoints=["divide and conquer"],
            difficulty="Medium",
            covered_keypoints=["divide and conquer"],
            missed_keypoints=[],
            score=100,
            mastery_label="strong",
            feedback="Describes divide and conquer approach.",
            follow_up=""
        ),
        # "invokes itself" should match "function calls itself"
        _create_example(
            question_text="What is recursion?",
            answer="A function that invokes itself repeatedly.",
            keypoints=["function calls itself"],
            difficulty="Easy",
            covered_keypoints=["function calls itself"],
            missed_keypoints=[],
            score=100,
            mastery_label="strong",
            feedback="Correctly describes recursive self-invocation.",
            follow_up=""
        ),
    ]

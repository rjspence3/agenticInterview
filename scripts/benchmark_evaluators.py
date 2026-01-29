#!/usr/bin/env python3
"""
Benchmark comparison of Heuristic vs LLM vs DSPy evaluators.

This script compares the three evaluator implementations on:
1. Accuracy: How well they match expected keypoint coverage
2. Latency: Response time per evaluation
3. Semantic understanding: Recognition of paraphrased concepts

Usage:
    python scripts/benchmark_evaluators.py
    python scripts/benchmark_evaluators.py --cases 10
    python scripts/benchmark_evaluators.py --evaluators heuristic,dspy
"""

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from models import Question


@dataclass
class BenchmarkResult:
    """Result of benchmarking a single evaluator."""
    evaluator_name: str
    num_cases: int
    accuracy: float  # Percentage of keypoints correctly identified
    avg_latency_ms: float
    paraphrase_recognition: float  # Percentage of paraphrased concepts recognized
    errors: int


def get_benchmark_cases() -> list[dict]:
    """
    Get benchmark test cases with ground truth.

    Returns list of dicts with:
    - question: Question object
    - answer: Candidate's answer
    - expected_covered: Set of keypoints that should be marked as covered
    - is_paraphrase: Whether the answer uses paraphrased terminology
    """
    cases = []

    # Case 1: List vs Tuple - paraphrased (key DSPy test)
    cases.append({
        "question": Question(
            id=1,
            text="What is the difference between a list and a tuple in Python?",
            competency="Python",
            difficulty="Easy",
            keypoints=["mutable vs immutable", "syntax differences"]
        ),
        "answer": "Lists can be changed after creation, tuples cannot. Lists use brackets, tuples use parentheses.",
        "expected_covered": {"mutable vs immutable", "syntax differences"},
        "is_paraphrase": True,
    })

    # Case 2: Recursion - literal match
    cases.append({
        "question": Question(
            id=2,
            text="What is recursion?",
            competency="Programming",
            difficulty="Medium",
            keypoints=["function calls itself", "base case", "recursive case"]
        ),
        "answer": "Recursion is when a function calls itself. It needs a base case to stop and a recursive case to continue.",
        "expected_covered": {"function calls itself", "base case", "recursive case"},
        "is_paraphrase": False,
    })

    # Case 3: Binary search - paraphrased
    cases.append({
        "question": Question(
            id=3,
            text="Explain binary search.",
            competency="Algorithms",
            difficulty="Medium",
            keypoints=["O(log n)", "divide and conquer", "sorted array"]
        ),
        "answer": "Binary search repeatedly splits the sorted array in half, achieving logarithmic time complexity.",
        "expected_covered": {"O(log n)", "divide and conquer", "sorted array"},
        "is_paraphrase": True,
    })

    # Case 4: Empty answer
    cases.append({
        "question": Question(
            id=4,
            text="Explain decorators in Python.",
            competency="Python",
            difficulty="Medium",
            keypoints=["function wrapping", "@ syntax"]
        ),
        "answer": "",
        "expected_covered": set(),
        "is_paraphrase": False,
    })

    # Case 5: Off-topic answer
    cases.append({
        "question": Question(
            id=5,
            text="What is the GIL in Python?",
            competency="Python",
            difficulty="Hard",
            keypoints=["Global Interpreter Lock", "thread safety", "performance impact"]
        ),
        "answer": "The weather is nice today. I enjoy sunny days.",
        "expected_covered": set(),
        "is_paraphrase": False,
    })

    # Case 6: Partial coverage - literal
    cases.append({
        "question": Question(
            id=6,
            text="Explain merge sort.",
            competency="Algorithms",
            difficulty="Hard",
            keypoints=["divide and conquer", "merge sorted halves", "O(n log n)"]
        ),
        "answer": "Merge sort uses divide and conquer to sort arrays. It has O(n log n) complexity.",
        "expected_covered": {"divide and conquer", "O(n log n)"},
        "is_paraphrase": False,
    })

    # Case 7: Generators - paraphrased
    cases.append({
        "question": Question(
            id=7,
            text="When would you use a generator?",
            competency="Python",
            difficulty="Medium",
            keypoints=["lazy evaluation", "memory efficiency", "yield keyword"]
        ),
        "answer": "Generators are great for large datasets because they process items one at a time instead of loading everything into memory. You create them with yield.",
        "expected_covered": {"lazy evaluation", "memory efficiency", "yield keyword"},
        "is_paraphrase": True,
    })

    return cases


def run_benchmark(
    evaluators: list[str],
    num_cases: Optional[int] = None,
    verbose: bool = True,
) -> dict[str, BenchmarkResult]:
    """
    Run benchmark comparison across evaluators.

    Args:
        evaluators: List of evaluator names to benchmark
        num_cases: Limit number of test cases (None for all)
        verbose: Print progress messages

    Returns:
        Dict mapping evaluator name to BenchmarkResult
    """
    from agents import EvaluatorAgent

    # Get test cases
    cases = get_benchmark_cases()
    if num_cases:
        cases = cases[:num_cases]

    if verbose:
        print("=" * 70)
        print("Evaluator Benchmark Comparison")
        print("=" * 70)
        print(f"\nTest cases: {len(cases)}")
        print(f"Evaluators: {', '.join(evaluators)}")

    results = {}

    for eval_name in evaluators:
        if verbose:
            print(f"\n{'─' * 70}")
            print(f"Benchmarking: {eval_name}")
            print("─" * 70)

        # Create evaluator
        evaluator = None
        if eval_name == "heuristic":
            evaluator = EvaluatorAgent()
        elif eval_name == "llm":
            try:
                from llm_evaluator import LLMEvaluatorAgent
                from llm_client import get_llm_client
                import settings
                is_valid, _ = settings.validate_llm_config()
                if not is_valid:
                    if verbose:
                        print("  Skipping LLM: not configured")
                    continue
                provider = settings.LLM_PROVIDER
                api_key = settings.get_api_key_for_provider(provider)
                client = get_llm_client(provider, api_key)
                evaluator = LLMEvaluatorAgent(client, settings.LLM_MODEL, settings.LLM_TEMPERATURE)
            except Exception as e:
                if verbose:
                    print(f"  Skipping LLM: {e}")
                continue
        elif eval_name == "dspy":
            try:
                from dspy_evaluator import DSPyEvaluatorAgent, DSPY_AVAILABLE
                if not DSPY_AVAILABLE:
                    if verbose:
                        print("  Skipping DSPy: not installed")
                    continue
                import settings
                is_valid, _ = settings.validate_dspy_config()
                if not is_valid:
                    if verbose:
                        print("  Skipping DSPy: not configured")
                    continue
                evaluator = DSPyEvaluatorAgent(
                    model=settings.DSPY_MODEL,
                    compiled_path=settings.DSPY_COMPILED_PATH,
                    temperature=settings.DSPY_TEMPERATURE
                )
            except Exception as e:
                if verbose:
                    print(f"  Skipping DSPy: {e}")
                continue

        if evaluator is None:
            continue

        # Run benchmark
        total_expected = 0
        total_correct = 0
        paraphrase_expected = 0
        paraphrase_correct = 0
        latencies = []
        errors = 0

        for i, case in enumerate(cases):
            if verbose:
                print(f"  Case {i+1}/{len(cases)}: {case['question'].text[:40]}...", end=" ")

            try:
                start_time = time.perf_counter()
                result = evaluator.evaluate(case["question"], case["answer"])
                latency = (time.perf_counter() - start_time) * 1000
                latencies.append(latency)

                # Calculate accuracy
                covered_set = {
                    kp.keypoint for kp in result.keypoints_coverage if kp.covered
                }
                expected_set = case["expected_covered"]

                # For empty expected, check that we didn't falsely identify any
                if not expected_set:
                    correct = len(covered_set) == 0
                    total_expected += 1
                    if correct:
                        total_correct += 1
                else:
                    # Count matching keypoints
                    for kp in case["question"].keypoints:
                        total_expected += 1
                        expected_covered = kp in expected_set
                        actual_covered = kp in covered_set
                        if expected_covered == actual_covered:
                            total_correct += 1

                        # Track paraphrase recognition
                        if case["is_paraphrase"] and expected_covered:
                            paraphrase_expected += 1
                            if actual_covered:
                                paraphrase_correct += 1

                if verbose:
                    print(f"Score: {result.score_0_100}, Latency: {latency:.0f}ms")

            except Exception as e:
                errors += 1
                if verbose:
                    print(f"ERROR: {e}")

        # Calculate results
        accuracy = (total_correct / total_expected * 100) if total_expected > 0 else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        paraphrase_rate = (paraphrase_correct / paraphrase_expected * 100) if paraphrase_expected > 0 else 0

        results[eval_name] = BenchmarkResult(
            evaluator_name=eval_name,
            num_cases=len(cases),
            accuracy=accuracy,
            avg_latency_ms=avg_latency,
            paraphrase_recognition=paraphrase_rate,
            errors=errors,
        )

    # Print summary
    if verbose and results:
        print("\n" + "=" * 70)
        print("RESULTS SUMMARY")
        print("=" * 70)
        print(f"\n{'Evaluator':<15} {'Accuracy':>10} {'Paraphrase':>12} {'Latency':>12} {'Errors':>8}")
        print("-" * 60)

        for name, result in results.items():
            print(
                f"{name:<15} {result.accuracy:>9.1f}% "
                f"{result.paraphrase_recognition:>11.1f}% "
                f"{result.avg_latency_ms:>10.0f}ms "
                f"{result.errors:>8}"
            )

        # Analysis
        print("\n" + "─" * 70)
        print("ANALYSIS")
        print("─" * 70)

        if "heuristic" in results and "dspy" in results:
            h = results["heuristic"]
            d = results["dspy"]

            print(f"\nParaphrase Recognition Improvement: {d.paraphrase_recognition - h.paraphrase_recognition:+.1f}%")
            print(f"Accuracy Improvement: {d.accuracy - h.accuracy:+.1f}%")
            print(f"Latency Cost: {d.avg_latency_ms - h.avg_latency_ms:+.0f}ms")

            if d.paraphrase_recognition > h.paraphrase_recognition:
                print("\n DSPy successfully recognizes paraphrased concepts!")
            else:
                print("\n Note: DSPy may need compilation for optimal performance.")
                print("   Run: python scripts/compile_dspy_evaluator.py")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark comparison of evaluators"
    )
    parser.add_argument(
        "--evaluators",
        type=str,
        default="heuristic,dspy",
        help="Comma-separated list of evaluators (default: heuristic,dspy)"
    )
    parser.add_argument(
        "--cases",
        type=int,
        default=None,
        help="Number of test cases (default: all)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )

    args = parser.parse_args()
    evaluators = [e.strip() for e in args.evaluators.split(",")]

    run_benchmark(
        evaluators=evaluators,
        num_cases=args.cases,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()

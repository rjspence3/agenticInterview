#!/usr/bin/env python3
"""
Compile DSPy evaluator with optimized prompts.

This script trains the DSPy evaluator using examples extracted from
the test suite, then saves the compiled module for production use.

Usage:
    python scripts/compile_dspy_evaluator.py
    python scripts/compile_dspy_evaluator.py --model gpt-4o
    python scripts/compile_dspy_evaluator.py --output custom_evaluator.json
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def compile_evaluator(
    model: str = "gpt-4o-mini",
    output_path: str = "compiled_evaluator.json",
    max_bootstrapped_demos: int = 4,
    max_labeled_demos: int = 8,
    train_ratio: float = 0.8,
    verbose: bool = True,
) -> None:
    """
    Compile the DSPy evaluator with optimized prompts.

    Args:
        model: LLM model to use for compilation
        output_path: Path to save compiled module
        max_bootstrapped_demos: Max examples to bootstrap from training
        max_labeled_demos: Max labeled examples in final prompt
        train_ratio: Fraction of data for training (rest is validation)
        verbose: Print progress messages
    """
    # Import DSPy and local modules
    try:
        import dspy
        from dspy.teleprompt import BootstrapFewShot
    except ImportError:
        print("Error: dspy-ai not installed. Run: pip install dspy-ai")
        sys.exit(1)

    from dspy_training import build_training_set
    from dspy_metrics import combined_metric
    from dspy_evaluator import KeypointEvaluation

    if verbose:
        print("=" * 60)
        print("DSPy Evaluator Compilation")
        print("=" * 60)

    # Configure DSPy LM
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key and "claude" in model.lower():
            lm = dspy.LM(model, api_key=api_key, temperature=0.0)
        else:
            print("Error: No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.")
            sys.exit(1)
    else:
        lm = dspy.LM(model, api_key=api_key, temperature=0.0)

    dspy.configure(lm=lm)

    if verbose:
        print(f"\nModel: {model}")
        print(f"Output: {output_path}")

    # Build training set
    if verbose:
        print("\n[1/4] Loading training data...")

    all_examples = build_training_set()
    split_idx = int(len(all_examples) * train_ratio)
    trainset = all_examples[:split_idx]
    valset = all_examples[split_idx:]

    if verbose:
        print(f"  Total examples: {len(all_examples)}")
        print(f"  Training: {len(trainset)}")
        print(f"  Validation: {len(valset)}")

    # Create optimizer
    if verbose:
        print("\n[2/4] Configuring optimizer...")

    optimizer = BootstrapFewShot(
        metric=combined_metric,
        max_bootstrapped_demos=max_bootstrapped_demos,
        max_labeled_demos=max_labeled_demos,
    )

    if verbose:
        print(f"  Max bootstrapped demos: {max_bootstrapped_demos}")
        print(f"  Max labeled demos: {max_labeled_demos}")

    # Create base module
    if verbose:
        print("\n[3/4] Compiling evaluator (this may take a few minutes)...")

    base_module = dspy.ChainOfThought(KeypointEvaluation)

    try:
        compiled = optimizer.compile(base_module, trainset=trainset)
    except Exception as e:
        print(f"\nError during compilation: {e}")
        sys.exit(1)

    if verbose:
        print("  Compilation complete!")

    # Evaluate on validation set
    if verbose:
        print("\n[4/4] Evaluating on validation set...")

    val_scores = []
    for example in valset:
        try:
            prediction = compiled(
                question_text=example.question_text,
                answer=example.answer,
                keypoints=example.keypoints,
                difficulty=example.difficulty,
            )
            score = combined_metric(example, prediction)
            val_scores.append(score)
        except Exception as e:
            if verbose:
                print(f"  Warning: Validation error - {e}")
            val_scores.append(0.0)

    avg_score = sum(val_scores) / len(val_scores) if val_scores else 0.0

    if verbose:
        print(f"  Validation score: {avg_score:.1%}")

    # Save compiled module
    output_file = Path(output_path)
    compiled.save(str(output_file))

    if verbose:
        print(f"\n{'=' * 60}")
        print(f"Compiled evaluator saved to: {output_file.absolute()}")
        print(f"{'=' * 60}")

    # Print usage instructions
    if verbose:
        print("\nUsage:")
        print("  1. Set EVALUATOR_TYPE=dspy in .env")
        print(f"  2. Ensure {output_path} is in the project root")
        print("  3. Restart the application")
        print("\nOr set DSPY_COMPILED_PATH to a custom location.")


def main():
    parser = argparse.ArgumentParser(
        description="Compile DSPy evaluator with optimized prompts"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="LLM model to use (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="compiled_evaluator.json",
        help="Output path for compiled module (default: compiled_evaluator.json)"
    )
    parser.add_argument(
        "--bootstrapped",
        type=int,
        default=4,
        help="Max bootstrapped demos (default: 4)"
    )
    parser.add_argument(
        "--labeled",
        type=int,
        default=8,
        help="Max labeled demos (default: 8)"
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Train/validation split ratio (default: 0.8)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages"
    )

    args = parser.parse_args()

    compile_evaluator(
        model=args.model,
        output_path=args.output,
        max_bootstrapped_demos=args.bootstrapped,
        max_labeled_demos=args.labeled,
        train_ratio=args.train_ratio,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()

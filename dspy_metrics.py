"""
DSPy optimization metrics for interview answer evaluation.

These metrics are used by BootstrapFewShot to optimize the evaluator
for accurate keypoint coverage detection and scoring.
"""

from typing import Any, Optional


def keypoint_f1_metric(
    example: Any,
    prediction: Any,
    trace: Optional[Any] = None
) -> float:
    """
    F1 score for keypoint classification accuracy.

    Measures how well the evaluator identifies which keypoints are covered
    vs missed in the candidate's answer.

    Args:
        example: Ground truth DSPy example with covered_keypoints
        prediction: Model prediction with covered_keypoints
        trace: Optional trace for debugging (unused)

    Returns:
        F1 score between 0.0 and 1.0
    """
    expected = set(getattr(example, 'covered_keypoints', []) or [])
    predicted = set(getattr(prediction, 'covered_keypoints', []) or [])

    # Handle edge case: both empty means correct prediction
    if not expected and not predicted:
        return 1.0

    # Handle edge case: one empty, one not
    if not expected or not predicted:
        return 0.0

    # Calculate true positives
    true_positives = len(expected & predicted)

    # Precision: of predicted covered, how many were actually covered?
    precision = true_positives / len(predicted)

    # Recall: of actually covered, how many did we predict?
    recall = true_positives / len(expected)

    # F1 score
    if precision + recall == 0:
        return 0.0

    return 2 * (precision * recall) / (precision + recall)


def score_accuracy_metric(
    example: Any,
    prediction: Any,
    trace: Optional[Any] = None
) -> float:
    """
    Penalize score deviations from ground truth.

    Measures how close the predicted score (0-100) is to the expected score.

    Args:
        example: Ground truth DSPy example with score field
        prediction: Model prediction with score field
        trace: Optional trace for debugging (unused)

    Returns:
        Accuracy between 0.0 and 1.0 (1.0 = exact match)
    """
    expected_score = getattr(example, 'score', 0)
    predicted_score = getattr(prediction, 'score', 0)

    # Handle string scores (DSPy may return strings)
    if isinstance(expected_score, str):
        try:
            expected_score = int(expected_score)
        except ValueError:
            expected_score = 0

    if isinstance(predicted_score, str):
        try:
            predicted_score = int(predicted_score)
        except ValueError:
            predicted_score = 0

    # Clamp to valid range
    expected_score = max(0, min(100, expected_score))
    predicted_score = max(0, min(100, predicted_score))

    # Calculate error as percentage of range
    error = abs(expected_score - predicted_score)

    # Return accuracy (1 - normalized error)
    return max(0.0, 1.0 - error / 100.0)


def mastery_label_metric(
    example: Any,
    prediction: Any,
    trace: Optional[Any] = None
) -> float:
    """
    Check if mastery label matches expected value.

    Args:
        example: Ground truth DSPy example with mastery_label
        prediction: Model prediction with mastery_label
        trace: Optional trace for debugging (unused)

    Returns:
        1.0 if labels match, 0.0 otherwise
    """
    expected = getattr(example, 'mastery_label', '').lower().strip()
    predicted = getattr(prediction, 'mastery_label', '').lower().strip()

    # Normalize variations
    label_map = {
        'strong': 'strong',
        'excellent': 'strong',
        'good': 'strong',
        'mixed': 'mixed',
        'partial': 'mixed',
        'moderate': 'mixed',
        'weak': 'weak',
        'poor': 'weak',
        'insufficient': 'weak',
    }

    expected_norm = label_map.get(expected, expected)
    predicted_norm = label_map.get(predicted, predicted)

    return 1.0 if expected_norm == predicted_norm else 0.0


def combined_metric(
    example: Any,
    prediction: Any,
    trace: Optional[Any] = None
) -> float:
    """
    Weighted combination of all evaluation metrics.

    This is the primary metric used for DSPy optimization.

    Weights:
    - Keypoint F1: 50% (most important - semantic understanding)
    - Score accuracy: 30% (numerical precision)
    - Mastery label: 20% (categorical correctness)

    Args:
        example: Ground truth DSPy example
        prediction: Model prediction
        trace: Optional trace for debugging

    Returns:
        Combined score between 0.0 and 1.0
    """
    f1 = keypoint_f1_metric(example, prediction, trace)
    score_acc = score_accuracy_metric(example, prediction, trace)
    mastery_acc = mastery_label_metric(example, prediction, trace)

    return 0.50 * f1 + 0.30 * score_acc + 0.20 * mastery_acc


def strict_keypoint_metric(
    example: Any,
    prediction: Any,
    trace: Optional[Any] = None
) -> float:
    """
    Strict metric that requires exact keypoint set match.

    Use this for validation to ensure no false positives/negatives.

    Args:
        example: Ground truth DSPy example
        prediction: Model prediction
        trace: Optional trace for debugging

    Returns:
        1.0 if exact match, 0.0 otherwise
    """
    expected_covered = set(getattr(example, 'covered_keypoints', []) or [])
    predicted_covered = set(getattr(prediction, 'covered_keypoints', []) or [])

    expected_missed = set(getattr(example, 'missed_keypoints', []) or [])
    predicted_missed = set(getattr(prediction, 'missed_keypoints', []) or [])

    covered_match = expected_covered == predicted_covered
    missed_match = expected_missed == predicted_missed

    return 1.0 if (covered_match and missed_match) else 0.0

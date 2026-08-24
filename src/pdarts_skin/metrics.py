"""Dependency-free classification metrics for reproducibility checks."""

from __future__ import annotations

from typing import Sequence


def _validate_targets(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    num_classes: int,
) -> None:
    if len(y_true) != len(y_pred):
        raise ValueError(
            "y_true and y_pred must have equal length"
        )

    if not y_true:
        raise ValueError("metric inputs must not be empty")

    if num_classes <= 1:
        raise ValueError(
            "num_classes must be greater than one"
        )

    valid = range(num_classes)

    if any(value not in valid for value in y_true):
        raise ValueError(
            "y_true contains an invalid class"
        )

    if any(value not in valid for value in y_pred):
        raise ValueError(
            "y_pred contains an invalid class"
        )


def confusion_matrix(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    num_classes: int,
) -> list[list[int]]:
    _validate_targets(y_true, y_pred, num_classes)

    matrix = [
        [0 for _ in range(num_classes)]
        for _ in range(num_classes)
    ]

    for truth, prediction in zip(y_true, y_pred):
        matrix[truth][prediction] += 1

    return matrix


def accuracy(
    y_true: Sequence[int],
    y_pred: Sequence[int],
) -> float:
    if len(y_true) != len(y_pred):
        raise ValueError(
            "y_true and y_pred must have equal length"
        )

    if not y_true:
        raise ValueError("metric inputs must not be empty")

    correct = sum(
        truth == prediction
        for truth, prediction in zip(y_true, y_pred)
    )

    return correct / len(y_true)


def weighted_f1(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    num_classes: int,
) -> float:
    matrix = confusion_matrix(
        y_true,
        y_pred,
        num_classes,
    )

    total_support = len(y_true)
    weighted_sum = 0.0

    for class_id in range(num_classes):
        true_positive = matrix[class_id][class_id]

        false_positive = sum(
            matrix[row][class_id]
            for row in range(num_classes)
            if row != class_id
        )

        false_negative = sum(
            matrix[class_id][column]
            for column in range(num_classes)
            if column != class_id
        )

        support = sum(matrix[class_id])

        denominator = (
            2 * true_positive
            + false_positive
            + false_negative
        )

        class_f1 = (
            0.0
            if denominator == 0
            else (2 * true_positive) / denominator
        )

        weighted_sum += support * class_f1

    return weighted_sum / total_support

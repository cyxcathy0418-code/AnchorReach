"""Reproducible human-vs-model correlation checks for the vision judge."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class DimensionScores:
    product_appearance: float
    logo_reference: float | None
    color_palette: float

    def validate(self, sample_id: str) -> None:
        values = {
            "product_appearance": self.product_appearance,
            "color_palette": self.color_palette,
        }
        if self.logo_reference is not None:
            values["logo_reference"] = self.logo_reference
        for field, value in values.items():
            if not 0 <= value <= 100:
                raise ValueError(f"{sample_id}.{field} must be between 0 and 100")

    def overall(self) -> float:
        if self.logo_reference is None:
            return (self.product_appearance * 0.5 + self.color_palette * 0.2) / 0.7
        return (
            self.product_appearance * 0.5
            + self.logo_reference * 0.3
            + self.color_palette * 0.2
        )


def _pearson(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        raise ValueError("Correlation requires at least two paired observations")
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    left_delta = [value - left_mean for value in left]
    right_delta = [value - right_mean for value in right]
    denominator = math.sqrt(
        sum(value * value for value in left_delta)
        * sum(value * value for value in right_delta)
    )
    if denominator == 0:
        raise ValueError("Correlation is undefined when either score series has zero variance")
    return sum(a * b for a, b in zip(left_delta, right_delta)) / denominator


def _average_ranks(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][1] == ordered[index][1]:
            end += 1
        average_rank = ((index + 1) + end) / 2
        for ordered_index in range(index, end):
            ranks[ordered[ordered_index][0]] = average_rank
        index = end
    return ranks


def validate_judge_correlation(
    human_scores: Mapping[str, DimensionScores],
    model_scores: Mapping[str, DimensionScores],
    *,
    threshold: float = 0.8,
    minimum_samples: int = 20,
) -> dict[str, object]:
    if set(human_scores) != set(model_scores):
        missing_human = sorted(set(model_scores) - set(human_scores))
        missing_model = sorted(set(human_scores) - set(model_scores))
        raise ValueError(
            f"Human/model sample IDs differ; missing_human={missing_human}, "
            f"missing_model={missing_model}"
        )

    sample_ids = sorted(human_scores)
    human_overall: list[float] = []
    model_overall: list[float] = []
    paired_rows: list[dict[str, object]] = []
    for sample_id in sample_ids:
        human = human_scores[sample_id]
        model = model_scores[sample_id]
        human.validate(sample_id)
        model.validate(sample_id)
        if (human.logo_reference is None) != (model.logo_reference is None):
            raise ValueError(f"{sample_id}.logo_reference must be absent in both files or present in both")
        human_value = human.overall()
        model_value = model.overall()
        human_overall.append(human_value)
        model_overall.append(model_value)
        paired_rows.append(
            {
                "sample_id": sample_id,
                "human_overall": round(human_value, 4),
                "model_overall": round(model_value, 4),
            }
        )

    if len(sample_ids) < 2:
        return {
            "status": "insufficient_sample",
            "trusted": False,
            "sample_count": len(sample_ids),
            "minimum_samples": minimum_samples,
            "threshold_exclusive": threshold,
            "pearson": None,
            "spearman": None,
            "paired_scores": paired_rows,
        }

    pearson = _pearson(human_overall, model_overall)
    spearman = _pearson(_average_ranks(human_overall), _average_ranks(model_overall))
    enough_samples = len(sample_ids) >= minimum_samples
    trusted = enough_samples and pearson > threshold and spearman > threshold
    return {
        "status": "trusted" if trusted else ("below_threshold" if enough_samples else "insufficient_sample"),
        "trusted": trusted,
        "sample_count": len(sample_ids),
        "minimum_samples": minimum_samples,
        "threshold_exclusive": threshold,
        "pearson": round(pearson, 6),
        "spearman": round(spearman, 6),
        "paired_scores": paired_rows,
    }

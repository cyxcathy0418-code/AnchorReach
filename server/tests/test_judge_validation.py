from __future__ import annotations

import pytest

from app.services.judge_validation import DimensionScores, validate_judge_correlation


def score(value: float, *, logo: bool = True) -> DimensionScores:
    return DimensionScores(
        product_appearance=value,
        logo_reference=value if logo else None,
        color_palette=value,
    )


def test_high_human_model_agreement_is_trusted() -> None:
    human = {f"sample-{index:02d}": score(30 + index * 3) for index in range(20)}
    model = {
        sample_id: score(human_score.product_appearance + (1 if index % 2 else -1))
        for index, (sample_id, human_score) in enumerate(human.items())
    }

    result = validate_judge_correlation(human, model)

    assert result["status"] == "trusted"
    assert result["trusted"] is True
    assert result["pearson"] > 0.8
    assert result["spearman"] > 0.8


def test_low_agreement_is_reported_without_adjusting_threshold() -> None:
    human = {f"sample-{index:02d}": score(20 + index * 3) for index in range(20)}
    model = {
        sample_id: score(90 - index * 3)
        for index, sample_id in enumerate(human)
    }

    result = validate_judge_correlation(human, model)

    assert result["status"] == "below_threshold"
    assert result["trusted"] is False
    assert result["pearson"] < 0
    assert result["spearman"] < 0


def test_small_dataset_remains_insufficient_even_with_perfect_correlation() -> None:
    human = {f"sample-{index}": score(20 + index * 10, logo=False) for index in range(5)}
    model = dict(human)

    result = validate_judge_correlation(human, model)

    assert result["status"] == "insufficient_sample"
    assert result["trusted"] is False
    assert result["pearson"] == 1.0
    assert result["spearman"] == 1.0


def test_mismatched_logo_contract_is_rejected() -> None:
    human = {"sample-1": score(80, logo=False), "sample-2": score(70, logo=False)}
    model = {"sample-1": score(80, logo=True), "sample-2": score(70, logo=False)}

    with pytest.raises(ValueError, match="logo_reference"):
        validate_judge_correlation(human, model, minimum_samples=2)

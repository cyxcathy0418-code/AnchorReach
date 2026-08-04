"""Explainable scoring and regeneration policy for AnchorReach phase 3."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from app.schemas.consistency import (
    AnchorDimension,
    ConsistencyCheckRequest,
    ConsistencyCheckResult,
    ConsistencyDimensionResult,
    ConsistencyJudgeMetadata,
    ConsistencyReport,
    JudgeAssessment,
    JudgeDimensionAssessment,
)
from app.services.vision_judge import JudgeRunResult, VisionJudgeError


BASE_WEIGHTS = {
    AnchorDimension.PRODUCT_APPEARANCE: 0.50,
    AnchorDimension.LOGO_REFERENCE: 0.30,
    AnchorDimension.COLOR_PALETTE: 0.20,
}
LOGO_HARD_FAILURE_SCORE_CAP = 59.0


def _active_dimensions(request: ConsistencyCheckRequest) -> list[AnchorDimension]:
    locked = set(request.anchor_block.locked_attributes)
    dimensions = [
        dimension
        for dimension in (
            AnchorDimension.PRODUCT_APPEARANCE,
            AnchorDimension.LOGO_REFERENCE,
            AnchorDimension.COLOR_PALETTE,
        )
        if dimension.value in locked
    ]
    if not dimensions:
        raise VisionJudgeError(
            "anchor_contract_invalid",
            "AnchorBlock must lock at least one visual anchor.",
            status_code=422,
        )
    if AnchorDimension.LOGO_REFERENCE in dimensions:
        if not request.anchor_block.visual_anchors.logo_reference:
            raise VisionJudgeError(
                "anchor_contract_invalid",
                "logo_reference is locked but contains no reference image.",
                status_code=422,
            )
    return dimensions


def _normalized_weights(
    dimensions: list[AnchorDimension],
) -> dict[AnchorDimension, float]:
    total = sum(BASE_WEIGHTS[dimension] for dimension in dimensions)
    return {
        dimension: BASE_WEIGHTS[dimension] / total
        for dimension in dimensions
    }


def _assessment_for_dimension(
    assessment: JudgeAssessment,
    dimension: AnchorDimension,
) -> JudgeDimensionAssessment:
    value = getattr(assessment, dimension.value)
    if value is None:
        raise VisionJudgeError(
            "judge_response_incomplete",
            f"Judge returned no assessment for locked dimension '{dimension.value}'.",
        )
    return value


def _build_regeneration_instruction(
    request: ConsistencyCheckRequest,
    failed_dimensions: list[ConsistencyDimensionResult],
) -> str:
    corrective_lines = []
    for dimension in failed_dimensions:
        issues = list(
            dict.fromkeys(
                dimension.hard_failure_reasons + dimension.discrepancies
            )
        )
        discrepancies = "; ".join(issues) or "score below policy threshold"
        score_context = (
            f"policy-adjusted score {dimension.score:.1f}/100 "
            f"(raw judge score {dimension.raw_judge_score:.1f}/100)"
            if dimension.hard_gate_triggered
            else f"score {dimension.score:.1f}/100"
        )
        corrective_lines.append(
            f"- {dimension.dimension.value}: {score_context}; {discrepancies}"
        )
    return (
        "AnchorReach consistency check failed. Regenerate the static asset and correct "
        "every failed locked anchor below. Do not merely recolor the previous output.\n"
        + "\n".join(corrective_lines)
        + "\n\nUse the original product and logo reference images again. Preserve all "
        "locked attributes exactly. The previous generated asset was: "
        f"{request.generated_asset_url}\n\nANCHOR_BLOCK:\n"
        + json.dumps(request.anchor_block.model_dump(mode="json"), ensure_ascii=False, indent=2)
    )


class VisionJudge(Protocol):
    async def evaluate(self, request: ConsistencyCheckRequest) -> JudgeRunResult: ...


class ConsistencyService:
    def __init__(self, judge: VisionJudge):
        self.judge = judge

    async def evaluate(
        self,
        request: ConsistencyCheckRequest,
    ) -> ConsistencyCheckResult:
        dimensions = _active_dimensions(request)
        weights = _normalized_weights(dimensions)
        judge_run: JudgeRunResult = await self.judge.evaluate(request)

        dimension_results: list[ConsistencyDimensionResult] = []
        for dimension in dimensions:
            assessment = _assessment_for_dimension(judge_run.assessment, dimension)
            raw_score = round(assessment.score, 2)
            hard_gate_triggered = (
                dimension == AnchorDimension.LOGO_REFERENCE
                and bool(assessment.hard_failure_codes)
            )
            policy_score = (
                min(raw_score, LOGO_HARD_FAILURE_SCORE_CAP)
                if hard_gate_triggered
                else raw_score
            )
            dimension_results.append(
                ConsistencyDimensionResult(
                    dimension=dimension,
                    score=policy_score,
                    raw_judge_score=raw_score,
                    weight=round(weights[dimension], 6),
                    passed=(
                        not hard_gate_triggered
                        and policy_score >= request.minimum_dimension_score
                    ),
                    hard_gate_triggered=hard_gate_triggered,
                    hard_failure_codes=assessment.hard_failure_codes,
                    hard_failure_reasons=assessment.hard_failure_reasons,
                    evidence=assessment.evidence,
                    discrepancies=assessment.discrepancies,
                )
            )

        overall_score = round(
            sum(result.score * weights[result.dimension] for result in dimension_results),
            2,
        )
        passed = (
            overall_score >= request.pass_threshold
            and all(result.passed for result in dimension_results)
        )
        attempts_remaining = request.max_attempts - request.attempt_number
        should_regenerate = not passed and attempts_remaining > 0
        failed_dimensions = [
            result
            for result in dimension_results
            if not result.passed or result.score < request.pass_threshold
        ]
        if not passed and not failed_dimensions:
            failed_dimensions = dimension_results

        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        report = ConsistencyReport(
            report_id=f"cr_{uuid4().hex}",
            attempt_number=request.attempt_number,
            overall_score=overall_score,
            pass_threshold=request.pass_threshold,
            minimum_dimension_score=request.minimum_dimension_score,
            passed=passed,
            dimensions=dimension_results,
            summary=judge_run.assessment.summary,
            judge_metadata=ConsistencyJudgeMetadata(
                provider=judge_run.provider,
                model=judge_run.model,
                evaluated_at=timestamp,
                latency_ms=judge_run.latency_ms,
                reference_images_used=judge_run.reference_images_used,
                generated_asset_url=request.generated_asset_url,
                raw_response_sha256=judge_run.raw_response_sha256,
                input_tokens=judge_run.input_tokens,
                output_tokens=judge_run.output_tokens,
                estimated_cost_usd=judge_run.estimated_cost_usd,
                configured_cost_limit_usd=judge_run.configured_cost_limit_usd,
            ),
        )
        return ConsistencyCheckResult(
            report=report,
            should_regenerate=should_regenerate,
            attempts_remaining=attempts_remaining,
            regeneration_instruction=(
                _build_regeneration_instruction(request, failed_dimensions)
                if should_regenerate
                else None
            ),
        )

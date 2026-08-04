from __future__ import annotations

import asyncio
import hashlib
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.consistency_router import get_consistency_service
from app.schemas.consistency import (
    ConsistencyCheckRequest,
    JudgeAssessment,
    JudgeDimensionAssessment,
    LogoHardFailureCode,
)
from app.schemas.structured_input import AnchorBlock
from app.services.consistency_service import ConsistencyService
from app.services.openai_vision_judge import OpenAIVisionJudge
from app.services.vision_judge import (
    JudgeRunResult,
    VisionJudgeError,
    _extract_model_text,
    _extract_result_url,
)


CLIENT = TestClient(app)


def test_live_muapi_video_field_is_parsed_as_text() -> None:
    payload = {"output": {"video": '{"summary":"visible evidence"}'}}

    assert _extract_model_text(payload) == '{"summary":"visible evidence"}'


def test_live_muapi_result_url_is_used_for_async_polling() -> None:
    payload = {
        "output": {
            "urls": {
                "get": "https://api.muapi.ai/provider-specific/result/req_123"
            }
        }
    }

    assert _extract_result_url(payload) == (
        "https://api.muapi.ai/provider-specific/result/req_123"
    )


def make_anchor_block(*, with_logo: bool = True) -> AnchorBlock:
    locked = ["product_appearance"]
    if with_logo:
        locked.append("logo_reference")
    locked.append("color_palette")
    return AnchorBlock.model_validate(
        {
            "visual_anchors": {
                "product_appearance": "Rectangular blue package with a silver cap",
                "logo_reference": "https://example.com/logo.png" if with_logo else None,
                "color_palette": ["#2455B4"],
            },
            "locked_attributes": locked,
            "extraction_metadata": {
                "source_images_used": ["https://example.com/product.png"],
                "color_source": "primary_color_field",
                "extraction_timestamp": "2026-08-03T00:00:00Z",
                "appearance_extraction_method": "deterministic_image_metadata",
            },
        }
    )


def make_assessment(
    *,
    product: float,
    logo: float | None,
    color: float,
    logo_hard_failure_codes: list[LogoHardFailureCode] | None = None,
    logo_hard_failure_reasons: list[str] | None = None,
) -> JudgeAssessment:
    def dimension(
        score: float,
        name: str,
        *,
        hard_failure_codes: list[LogoHardFailureCode] | None = None,
        hard_failure_reasons: list[str] | None = None,
    ) -> JudgeDimensionAssessment:
        return JudgeDimensionAssessment(
            score=score,
            evidence=[f"Visible {name} evidence"],
            discrepancies=[] if score >= 80 else [f"{name} differs from reference"],
            hard_failure_codes=hard_failure_codes or [],
            hard_failure_reasons=hard_failure_reasons or [],
        )

    return JudgeAssessment(
        product_appearance=dimension(product, "product"),
        logo_reference=(
            dimension(
                logo,
                "logo",
                hard_failure_codes=logo_hard_failure_codes,
                hard_failure_reasons=logo_hard_failure_reasons,
            )
            if logo is not None
            else None
        ),
        color_palette=dimension(color, "color"),
        summary="Deterministic fake judge result for policy testing.",
    )


class FakeJudge:
    def __init__(self, assessment: JudgeAssessment):
        self.assessment = assessment

    async def evaluate(self, request: ConsistencyCheckRequest) -> JudgeRunResult:
        sources = list(request.anchor_block.extraction_metadata.source_images_used)
        if request.anchor_block.visual_anchors.logo_reference:
            sources.append(request.anchor_block.visual_anchors.logo_reference)
        sources.append(request.generated_asset_url)
        return JudgeRunResult(
            assessment=self.assessment,
            model="fake-vision-judge",
            latency_ms=12,
            reference_images_used=sources,
            raw_response_sha256=hashlib.sha256(b"fake").hexdigest(),
        )


def evaluate(
    assessment: JudgeAssessment,
    *,
    with_logo: bool = True,
    attempt_number: int = 1,
) -> object:
    request = ConsistencyCheckRequest(
        anchor_block=make_anchor_block(with_logo=with_logo),
        generated_asset_url="https://example.com/generated.png",
        attempt_number=attempt_number,
    )
    return asyncio.run(ConsistencyService(FakeJudge(assessment)).evaluate(request))


def test_weighted_score_with_logo_passes() -> None:
    result = evaluate(make_assessment(product=90, logo=80, color=70))

    assert result.report.overall_score == 83.0
    assert [dimension.weight for dimension in result.report.dimensions] == [0.5, 0.3, 0.2]
    assert result.report.passed is True
    assert result.should_regenerate is False
    assert result.regeneration_instruction is None


def test_logo_hard_failure_caps_score_and_forces_failure() -> None:
    assessment = make_assessment(
        product=94,
        logo=96,
        color=88,
        logo_hard_failure_codes=[LogoHardFailureCode.CORE_COLOR_CHANGED],
        logo_hard_failure_reasons=[
            "The multicolor reference logo was rendered as white on blue."
        ],
    )
    request = ConsistencyCheckRequest(
        anchor_block=make_anchor_block(),
        generated_asset_url="https://example.com/generated.png",
        minimum_dimension_score=50,
    )

    result = asyncio.run(ConsistencyService(FakeJudge(assessment)).evaluate(request))
    logo_result = next(
        dimension
        for dimension in result.report.dimensions
        if dimension.dimension.value == "logo_reference"
    )

    assert result.report.scoring_policy_version == "logo_hard_gate_v2"
    assert logo_result.raw_judge_score == 96
    assert logo_result.score == 59
    assert logo_result.hard_gate_triggered is True
    assert logo_result.passed is False
    assert logo_result.hard_failure_codes == [
        LogoHardFailureCode.CORE_COLOR_CHANGED
    ]
    assert result.report.overall_score == 82.3
    assert result.report.passed is False
    assert result.should_regenerate is True
    assert "raw judge score 96.0" in result.regeneration_instruction
    assert "rendered as white on blue" in result.regeneration_instruction


def test_weights_are_normalized_when_logo_is_absent() -> None:
    result = evaluate(
        make_assessment(product=90, logo=None, color=80),
        with_logo=False,
    )

    assert result.report.overall_score == 87.14
    assert [dimension.weight for dimension in result.report.dimensions] == [0.714286, 0.285714]
    assert result.report.passed is True


def test_only_locked_attributes_are_scored() -> None:
    anchor = make_anchor_block(with_logo=False).model_copy(
        update={"locked_attributes": ["color_palette"]}
    )
    request = ConsistencyCheckRequest(
        anchor_block=anchor,
        generated_asset_url="https://example.com/generated.png",
    )
    result = asyncio.run(
        ConsistencyService(
            FakeJudge(make_assessment(product=10, logo=None, color=90))
        ).evaluate(request)
    )

    assert len(result.report.dimensions) == 1
    assert result.report.dimensions[0].dimension.value == "color_palette"
    assert result.report.overall_score == 90
    assert result.report.passed is True


def test_minimum_dimension_failure_creates_specific_retry_instruction() -> None:
    result = evaluate(make_assessment(product=98, logo=59, color=98))

    assert result.report.overall_score == 86.3
    assert result.report.passed is False
    assert result.should_regenerate is True
    assert result.attempts_remaining == 2
    assert "logo_reference" in result.regeneration_instruction
    assert "logo differs from reference" in result.regeneration_instruction
    assert "ANCHOR_BLOCK" in result.regeneration_instruction


def test_final_attempt_never_requests_another_regeneration() -> None:
    result = evaluate(
        make_assessment(product=45, logo=45, color=45),
        attempt_number=3,
    )

    assert result.report.passed is False
    assert result.should_regenerate is False
    assert result.attempts_remaining == 0
    assert result.regeneration_instruction is None


def test_consistency_endpoint_returns_explainable_report() -> None:
    service = ConsistencyService(FakeJudge(make_assessment(product=88, logo=84, color=82)))
    app.dependency_overrides[get_consistency_service] = lambda: service
    try:
        response = CLIENT.post(
            "/api/v1/anchor-reach/consistency-check",
            json={
                "anchor_block": make_anchor_block().model_dump(mode="json"),
                "generated_asset_url": "https://example.com/generated.png",
            },
        )
    finally:
        app.dependency_overrides.pop(get_consistency_service, None)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["report"]["passed"] is True
    assert len(payload["report"]["dimensions"]) == 3
    assert payload["report"]["judge_metadata"]["raw_response_sha256"]


def test_provider_failure_never_fabricates_a_score(monkeypatch) -> None:
    monkeypatch.delenv("MU_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("ANCHORREACH_JUDGE_PROVIDER", "openai")
    response = CLIENT.post(
        "/api/v1/anchor-reach/consistency-check",
        json={
            "anchor_block": make_anchor_block().model_dump(mode="json"),
            "generated_asset_url": "https://example.com/generated.png",
        },
    )

    assert response.status_code == 503
    payload = response.json()
    assert payload["error"]["code"] == "judge_api_key_missing"
    assert "score" not in payload
    assert "automatic regeneration did not start" in payload["error"]["message"]


def test_openai_judge_requires_explicit_cost_authorization() -> None:
    request = ConsistencyCheckRequest(
        anchor_block=make_anchor_block(),
        generated_asset_url="https://example.com/generated.png",
    )
    judge = OpenAIVisionJudge(api_key="test-key", cost_limit_usd=0)

    with pytest.raises(VisionJudgeError) as exc_info:
        asyncio.run(judge.evaluate(request))

    assert exc_info.value.code == "judge_cost_not_authorized"


def test_openai_judge_returns_structured_score_and_usage() -> None:
    assessment = make_assessment(product=84, logo=31, color=88)

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.openai.com/v1/responses"
        assert request.headers["Authorization"] == "Bearer test-key"
        sent = json.loads(request.content)
        assert sent["model"] == "gpt-5.4-mini"
        assert sent["store"] is False
        assert sent["max_output_tokens"] == 1200
        assert sent["text"]["format"]["strict"] is True
        dimension_schema = sent["text"]["format"]["schema"]["$defs"]["dimension"]
        assert "hard_failure_codes" in dimension_schema["required"]
        assert "hard_failure_reasons" in dimension_schema["required"]
        image_parts = [
            part
            for part in sent["input"][1]["content"]
            if part["type"] == "input_image"
        ]
        assert len(image_parts) == 3
        assert all(part["detail"] == "high" for part in image_parts)
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": assessment.model_dump_json(),
                            }
                        ],
                    }
                ],
                "usage": {"input_tokens": 6200, "output_tokens": 310},
            },
        )

    transport = httpx.MockTransport(handler)
    judge = OpenAIVisionJudge(
        api_key="test-key",
        cost_limit_usd=0.02,
        transport=transport,
    )
    request = ConsistencyCheckRequest(
        anchor_block=make_anchor_block(),
        generated_asset_url="https://example.com/generated.png",
    )

    result = asyncio.run(judge.evaluate(request))

    assert result.provider == "openai_responses_vision"
    assert result.assessment.logo_reference.score == 31
    assert result.input_tokens == 6200
    assert result.output_tokens == 310
    assert result.estimated_cost_usd == 0.006045
    assert result.configured_cost_limit_usd == 0.02


def test_invalid_consistency_request_uses_specific_error_contract() -> None:
    response = CLIENT.post(
        "/api/v1/anchor-reach/consistency-check",
        json={
            "anchor_block": make_anchor_block().model_dump(mode="json"),
            "generated_asset_url": "https://example.com/generated.png",
            "attempt_number": 4,
            "max_attempts": 3,
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "consistency_request_validation_failed"
    assert "score" in payload["error"]["message"]
